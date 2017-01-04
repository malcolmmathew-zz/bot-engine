# bot-engine

Python engine for quick, simple, and dynamic generation of Facebook Messenger bots.

## Inspiration
While developing a Messenger bot for a charity in the Greater Toronto Area, we realized how Facebook Messenger was a powerful outlet for small businesses and charities to converse with their customers/users. As well, we realized that there was a semi-standard approach to writing the logic for Messenger bots with a sufficient amount of functionality (i.e. postback and message list support).

Thinking that it would be useful and cost-efficient for small businesses and charities to use a black box which dynamically generated Messenger bots, we began working towards developing a tool/engine/API for bot creation through simple JSON specification.

## Bot Creation Workflow

#### Repository

1. Clone this repository to your local or remote machine.

#### Facebook Page Creation

1. Navigate to https://www.facebook.com/pages/create/

2. Choose an appropriate category corresponding to your page. For testing use *Cause or Community*.

3. Go through the prescribed setup process (if required).

#### Facebook Application Creation

1. Navigate to the Facebook Developer quickstart page: https://developers.facebook.com/quickstarts/?platform=web

2. Click *Skip and Create Application ID*.

3. Specify your 'Application Name', 'Contact Email', and 'Category' (e.g. Communication).

4. Enter the captcha.

5. Within *Product Setup*, click *Get Started* next to *Messenger*. You will be redirected to the Messenger Product page.

6. Under *Token Generation*, select your previously created page.

7. Enable all mandatory permissions, in case a prompt appears.

8. Add the outputted 'Page Access Token' to your clipboard.

#### Engine Configuration

1. Modify evars.sh to include the newly retrieved Page Access Token.

2. Specify a custom Verification Token in evars.sh.

3. Run the run.sh bash script and retrieve the outputted web url. This bash script will wipe all collections in the database (dev + testing feature which will be removed in production).

#### Facebook Application Update

1. Navigate to the previously opened Messenger Product page. 

2. Click *Setup Webhooks* within the *Webhooks* section.

3. Specify the previously outputted application url under 'Callback URL'.

4. Specify the custom verification token under 'Verify Token'.

5. Click the *messages*, *message_deliveries*, *messaging_optins*, *messaging_postbacks*, and *message_reads* options under 'Subscription Fields'.

6. under *Webhooks*, choose your previously created page and click *Subscribe* such that the page subscribes to your newly created webhook.

#### Bot Communication

1. Navigate to your page on Facebook and click *Message* to begin communicating with your bot.

## Current State

The engine and associated process currently exists as a set of bash scripts and Python modules which can be configured (via parameters) to generate a Facebook Messenger bot. Due to cost limitations, there exists a single database (and collection) for data storage. 

The next iteration of this project would include packaging the engine and template modules into a Flask application server, and deploying said server on a remote machine (e.g. thin EC2 instance, Amazon Lightsail). The deployed server would expose a simple API allowing JSON passing, while generating subprocesses for handling the generated files and deploying the bot to Heroku.
