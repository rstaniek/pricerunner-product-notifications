
import requests, json, datetime, sys, getopt, smtplib, ssl, email, os.path, datetime
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class ConfigManager():
    FILE = 'config.json'

    def __init__(self, *args, **kwargs):
        self.cfg = None
        self._load()
        super().__init__(*args, **kwargs)

    def _load(self):
        try:
            with open(ConfigManager.FILE, 'r') as f:
                cfg = json.load(f)
                self.cfg = cfg
        except:
            print('An error occured while loading the script config file [{}]. It either does not exist or is locked by another process. Do something about this!'.format(ConfigManager.FILE))
            sys.exit(2)
    
    def _update_config(self):
        with open(ConfigManager.FILE, 'w') as f:
            json.dump(self.cfg, f, indent=4)

    def as_string(self):
        return json.dumps(self.cfg, indent=4)

    def get_gmail_cfg(self):
        return self.cfg['gmail']

    def get_program_cfg(self):
        return self.cfg['program']

    def get_mail_bcc(self):
        return self.cfg['program']['notif_bcc']

    def add_mail_bcc(self, bcc):
        self.cfg['program']['notif_bcc'].append(bcc)
        print('Adding new bcc [{}] to config'.format(bcc))
        self._update_config()
        print('List of BCCs updated!')
        return True

    def del_mail_bcc(self, bcc):
        self.cfg['program']['notif_bcc'].remove(bcc)
        print('Removing[{}] from config'.format(bcc))
        self._update_config()
        print('List of BCCs updated!')
        return True

    def set_mail_receiver(self, r):
        self.cfg['program']['receiver'] = r
        print('Setting the new receiver as: {}'.format(r))
        self._update_config()
        print('Receiver changed!')
        return True

class EmailBuilder():
    PLAIN = 'plain'
    HTML = 'html'

    def __init__(self, sender, receiver, *args, **kwargs):
        self.message = MIMEMultipart()
        self.message['From'] = sender
        self.message['To'] = receiver
        super().__init__(*args, **kwargs)

    def withSubject(self, subject):
        self.message['Subject'] = subject
        return self

    def withBcc(self, bcc):
        if bcc is not None and len(bcc) != 0:
            cc_str = ', '.join(['<{}>'.format(x) for x in bcc])
            self.message['Bcc'] = cc_str
        return self

    def withBody(self, message, mime_type = 'plain'):
        self.message.attach(MIMEText(message, mime_type))
        return self

    def withAttachment(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            self.message.attach(part)
            return self
    
    def build(self):
        print('built message: \n{}\n'.format(self.message.as_string()))
        return self.message.as_string()

class GmailHandler():
    def __init__(self, receiver_addr = None, *args, **kwargs):
        self.receiver = receiver_addr
        self.cfg = ConfigManager().get_gmail_cfg()
        self.server = smtplib.SMTP(self.cfg['smtp_server'], self.cfg['port'])
        self._connect()
        super().__init__(*args, **kwargs)

    def _connect(self):
        try:
            context = ssl.create_default_context()
            self.server = smtplib.SMTP(self.cfg['smtp_server'], self.cfg['port'])
            self.server.ehlo()
            self.server.starttls(context=context)
            self.server.ehlo()
        except Exception as e:
            print(e)

    def _chck_addr(self, receiver_addr):
        addr = receiver_addr if receiver_addr is not None else self.receiver
        if addr is None:
            print('Receiver not specified!!!')
            self.server.quit()
            sys.exit(2)
        return addr

    def send_plain(self, subject, msg, receiver_addr = None):
        self._connect()
        addr = self._chck_addr(receiver_addr)
        message = self.cfg['template']['_default']
        message = message.format(subject=subject, message=msg)
        print('Sending notification to {}'.format(addr))
        try:
            self.server.login(self.cfg['email_addr'], self.cfg['password'])
            self.server.sendmail(self.cfg['email_addr'], addr, message)
            print('Email notification sent!')
        except Exception as e:
            print(e)
        finally:
            self.server.quit()

    def send(self, msg, receiver_addr = None):
        self._connect()
        addr = self._chck_addr(receiver_addr)
        print('Sending notification to {}'.format(addr))
        try:
            self.server.login(self.cfg['email_addr'], self.cfg['password'])
            self.server.sendmail(self.cfg['email_addr'], addr, msg)
            print('Email notification sent!')
        except Exception as e:
            print(e)
        finally:
            self.server.quit()
        

class ProductInfo():
    BASE_URL = 'https://www.pricerunner.dk'

    def __init__(self, price, delivery, merchantRatingCount, retailerName, retailerInfoURL, retailerClickout, currency, safeBuy, productName, *args, **kwargs):
        self.price = price
        self.currency = currency
        self.delivery = delivery
        self.merchantRatingCount = merchantRatingCount
        self.retailerName = retailerName
        self.retailerInfoURL = retailerInfoURL
        self.retailerClickout = retailerClickout
        self.safeBuy = safeBuy
        self.productName = productName

    @classmethod
    def from_dict(cls, d):
        return cls(d['price'], d['delivery'], d['merchantRatingCount'], d['retailerName'], d['retailerInfoUrl'], d['retailerClickout'], d['currency'], d['safeBuy'], d['productName'])

    def info(self):
        return 'Price: {} {} @ {},\tsafe buy: {};\tdirect URL: {}{}\n'.format(self.price, self.currency, self.retailerName, 'YES' if self.safeBuy else 'NO', ProductInfo.BASE_URL, self.retailerClickout)

    def cheaper(self, offer):
        return float(offer.price) < float(self.price)

    
class Program():
    URL_PATH = 'https://www.pricerunner.dk/public/v3/pl/{}/dk?urlName={}&offer_sort=price&groupbyscope=true'
    PRODUCT_ID = '543-3827489'
    URL_NAME = 'Kamera-Objektiver/Tamron-SP-70-200mm-F-2.8-Di-VC-USD-G2-for-Nikon-Sammenlign-Priser'

    def __init__(self, check_interval, url = None, product_id = None, url_name = None, *args, **kwargs):
        self.interval = check_interval
        self.current_cheapest = ProductInfo(99999999.99, '', 0, '', '', '', '', False, '')
        if url is not None:
            self.url = url
        elif product_id is not None and url_name is not None:
            self.url = Program.URL_PATH.format(product_id, url_name)
        else:
            self.url = Program.URL_PATH.format(Program.PRODUCT_ID, Program.URL_NAME)
        self.cfg = ConfigManager().get_program_cfg()
        self.mail_client = GmailHandler(self.cfg['receiver'])
        self.infinite_job = False
        super().__init__(*args, *kwargs)

    def get_avail_offers(self):
        r = requests.get(self.url)
        response = json.loads(r.text)
        return [ProductInfo.from_dict(offer) for offer in response['nationalOffers']['offers'] if offer['stock'] != 'Out Of Stock']

    def update_cheapest(self):
        old = self.current_cheapest
        offers = self.get_avail_offers()
        for offer in offers:
            self.current_cheapest = offer if self.current_cheapest.cheaper(offer) else self.current_cheapest
        print('[{}] Current cheapest: {}'.format(datetime.datetime.now(), self.current_cheapest.info()))
        if old != self.current_cheapest:
            if self.cfg['receiver'] is not None and self.cfg['receiver'] != '' and self.cfg['receiver'] != ' ':
                self.send_notification()
            else:
                print('\tNo receiver specified, aborting notification!!')

    def send_notification(self):
        sender = ConfigManager().get_gmail_cfg()['email_addr']
        msg_from_template = ConfigManager().get_gmail_cfg()['template']['_html_cheper_product_notif']
        msg_from_template = msg_from_template.format(
            product_name=self.current_cheapest.productName, 
            price=self.current_cheapest.price, 
            currency=self.current_cheapest.currency, 
            full_url='{}{}'.format(ProductInfo.BASE_URL, self.current_cheapest.retailerClickout), 
            delivery=self.current_cheapest.delivery, 
            retailer_name=self.current_cheapest.retailerName,
            safe_buy= 'YES' if self.current_cheapest.safeBuy else 'NO')
        msg = EmailBuilder(receiver=self.cfg['receiver'], sender=sender).withSubject('New offer found!').withBody(msg_from_template, EmailBuilder.HTML).withBcc(self.cfg['notif_bcc']).build()
        self.mail_client.send(msg)

    def send_job_terminated_notif(self):
        if self.cfg['receiver'] is not None and self.cfg['receiver'] != '' and self.cfg['receiver'] != ' ':
            sender = ConfigManager().get_gmail_cfg()['email_addr']
            msg_from_template = ConfigManager().get_gmail_cfg()['template']['_html_job_terminated_notif']
            msg_from_template = msg_from_template.format(
                product_name=self.current_cheapest.productName,
                price=self.current_cheapest.price, 
                currency=self.current_cheapest.currency,
                retailer_name=self.current_cheapest.retailerName,
                timestamp=datetime.datetime.now())
            msg = EmailBuilder(receiver=self.cfg['receiver'], sender=sender).withSubject('Pricerunner job finished!').withBody(msg_from_template, EmailBuilder.HTML).build()
            self.mail_client.send(msg)
        else:
            print('\tNo receiver specified, aborting notification!!')

    def run(self, job_length_minutes, is_indefinite = False):
        self.infinite_job = is_indefinite
        if is_indefinite == False:
            sched = BackgroundScheduler()
            sched.add_job(self.update_cheapest, 'interval', minutes = self.interval)
            sched.start()
            try:
                print('Setting up a job for {} minutes'.format(job_length_minutes))
                sleep(job_length_minutes * 60)
            finally:
                sched.shutdown()
                self.send_job_terminated_notif()
        else:
            while True:
                sleep(self.interval * 60)
                self.update_cheapest()

def print_help():
    text = ('pricerunner-price-service.py\n'
        'REQUIRED ARGUMENTS:\n'
            '\t-i | --interval <interval>\tType: Float\texample: 5\n'
            '\t-l | --job_length <job lenght>\tType: Float\texample: 10\tNOTE! Might be replaced with --indefinite\n'
        'OPTIONAL ARGUMETS:\n'
            '\tNOTE! Use either --url param OR a combination of --url_name AND --product_id!!!\n'
            '\t-u | --url <url>\t\tType: String\texample: "https://www.pricerunner.dk/public/v3/pl/543-3827489/dk?urlName=Kamera-Objektiver/Tamron-SP-70-200mm-F-2.8-Di-VC-USD-G2-for-Nikon-Sammenlign-Priser&offer_sort=price&groupbyscope=true"\n'
            '\t--url_name <query param>\tType: String\texample: "Kamera-Objektiver/Tamron-SP-70-200mm-F-2.8-Di-VC-USD-G2-for-Nikon-Sammenlign-Priser"\n'
            '\t--product_id <ID>\t\tType: String\texample: "543-3827489"\n'
            '\t--indefinite\t\tNote: Use when the program shall never halt\n'
        'ADDITIONAL OPERATIONS:\n'
            '\t-r | --receiver <email>\tType: String\texample: example@email.com\tNote: sets the receiver to the selected one, use white space for not having any receiver at all\n'
            '\t--cfg\tNote: Display current configuration\n'
            '\t--bcc\tNote: Used for editing BCC recipents\n'
                '\t\t--add <bcc>\tType: String\texample: example@email.com\tNote: adds an extra bcc recipent. Works with --bcc\n'
                '\t\t--del <bcc>\tType: String\texample: example@email.com\tNote: deletes existing bcc from the list. Works with --bcc\n')
    print(text)

def main(args):
    interval = None
    job_length = None
    url = None
    url_name = None
    product_id = None
    bcc_operation = False
    str_add = None
    str_del = None
    str_receiver = None
    job_indefinite = False
    show_cfg = False
    try:
        opts, args = getopt.getopt(args, "?hi:l:u:r:", ['interval=', 'job_length=', 'url=', 'product_id=', 'url_name=', 'bcc', 'add=', 'del=', 'receiver=', 'indefinite', 'cfg'])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h' or opt == '?':
            print_help()
            sys.exit(0)
        elif opt in ('-i', '--interval'):
            try:
                interval = float(arg)
            except:
                print_help()
                sys.exit(2)
        elif opt in ('-l', '--job_length'):
            try:
                job_length = float(arg)
            except:
                print_help()
                sys.exit(2)
        elif opt in ('-u', '--url'):
            url = str(arg)
        elif opt == '--product_id':
            product_id = str(arg)
        elif opt == '--url_name':
            url_name = str(arg)
        elif opt == '--bcc':
            bcc_operation = True
        elif opt == '--add':
            str_add = str(arg)
        elif opt == '--del':
            str_del = str(arg)
        elif opt in ('-r', '--receiver'):
            str_receiver = str(arg)
        elif opt == '--indefinite':
            job_indefinite = True
        elif opt == '--cfg':
            show_cfg = True
    if bcc_operation:
        cfg = ConfigManager()
        if str_add is not None:
            cfg.add_mail_bcc(str_add)
        elif str_del is not None:
            cfg.del_mail_bcc(str_del)
        else:
            print('\nList of current Bcc:\n\t{}\n'.format(cfg.get_mail_bcc()))
        sys.exit(0)
    elif str_receiver is not None:
        cfg = ConfigManager()
        cfg.set_mail_receiver(str_receiver)
        sys.exit(0)
    elif show_cfg:
        print(ConfigManager().as_string())
        sys.exit(0)


    #actual program preparation starts here!!!
    if interval is None:
        if job_length is None and job_indefinite is False:
            print('Missing required arguments!!!')
            print_help()
            sys.exit(2)
    if url is not None:   
        p = Program(interval ,url=url)
    elif url_name is not None and product_id is not None:
        p = Program(interval, url_name=url_name, product_id=product_id)
    else:
        p = Program(interval)
    p.run(job_length, job_indefinite)

if __name__ == "__main__":
    main(sys.argv[1:])
