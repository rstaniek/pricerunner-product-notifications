# Pricerunner Product Notifications
A python job for tracking a product from [Pricerunner.dk](https://www.pricerunner.dk/) and sends an email notification when the price changes to a lower one.
## Setup
There is an email account required for sending out the notifications. In the current revision, it is confirmed that this script works with Gmail services.

### E-mail account [GMAIL] :e-mail:
It is advised to create a throaway account as the credentials might be leaked if not handled properly, account might be blacklisted for possible spamming and on top of that, certain security measure have to be disabled in order for this script to work. Gmail settings can be adjusted [here](https://myaccount.google.com/lesssecureapps).

### Python libraries
When in the project directory, run the following command to make sure, all the necessary Python packages are installed.
```ps
pip install -r requirements.txt
```

### Configuration of the script
:white_check_mark: On first run of the script you should first configure the recipients, email server settings and mail templates.
To do so, go to the `config.json` file and edit the following properties: 
* `gmail` > `email_addr` - email address of the sender account
* `gmail` > `password` - password to that account
* `gmail` > `template` > `_html` - Either edit, replace or use the provided template. Remeber to ensure that the binds for python variables remain intact, or otherwise are also replaced in the script:heavy_exclamation_mark: 

To configure a recipient and a Bcc list, you can execute it anytime through the script by using the following commands:

:arrow_forward: set a receiver email address (Required!)<br>
```ps
python ./pricerunner-price-service.py --receiver "example@email.com"
```
:arrow_forward: display a list of bcc
```ps
python ./pricerunner-price-service.py --bcc
```
:arrow_forward: add a new bcc recipient
```ps
python ./pricerunner-price-service.py --bcc --add "example@email.com"
```
:arrow_forward: delete an *existing* bcc recipient
```ps
python ./pricerunner-price-service.py --bcc --del "example@email.com"
```

## Sample usage

The script itself executes as either a time restricted job or in continuous mode. Upon invoking the main functionality a time interval is to be specified, which determines how often the pricerunner API will be probed for new offers. Here are some of the ways to execute the pricerunner script:

:zap:`python ./pricerunner-price-service.py -i 5 -l 360`

:zap:`python ./pricerunner-price-service.py -i 5 -l 360 --product_id "<id param>" --url_name "<url name param>"`

:zap:`python ./pricerunner-price-service.py -i 5 --indefinite --product_id "<id param>" --url_name "<url name param>"`

### Fully working example

:zap:`python ./pricerunner-price-service.py -i 0.02 -l 0.4 --product_id "1-4676650" --url_name "Apple-iPhone-XR-64GB-Sammenlign-Priser"`

## Command line argumets

In this section, there are listed all the currently supported start cmd arguments:

short | long | param | data type | example | note
------|------|-------|-----------|---------|-----
-i | --interval | minutes | Float | 5 or 0.2 | Required
-l | --job_length | minutes | Float | 0.5 or 60 | Required (unless replaced with --indefinite)
:x: | --indefinite | :x: | :x: | :x: | Executes the job without end, untill manual halt. Replaces the -l argument
:x: | --url_name | product url name | String | Product-name-param-1-65 | Must be used in tandem with --product_id
:x: | --product_id | product_id | String | 12314_3 | Must be used in tandem with --url_name
-h or -? | :x: | :x: | :x: | :x: | Prints help text
:x: | --cfg | :x: | :x: | :x: | Display current script configuration
-r | --receiver | email | String | example@email.com | Sets an email address of the notification recipient
:x: | --bcc | :x: | :x: | :x: | Display a list of bcc recipients
:x: | --bcc --add | email | String | example@email.com | Adds a recipient to the bcc group. Must be used with --bcc argument
:x: | --bcc --del | email | String | example@email.com | Removes an existing recipient from the bcc group
