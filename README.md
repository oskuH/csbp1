# Cyber Security Base Project 1

Personal course project for the 2024 edition of [Cyber Security Base](https://cybersecuritybase.mooc.fi/), a massive open online course by the University of Helsinki.
This is a pure django application with some intentional cyber security vulnerabilities. The purpose of this README is to cover all the flaws and their fixes but there are also some assisting comments in the code.
The reader is excpected to have some programming experience.

## Introduction

Welcome to Abilityhub. This app simulates an imaginary web site where individual users can buy and sell services amongst each other. Each user has a profile where they can advertise their services through their description or uploaded images. Communication between users is carried out via the app’s own messaging platform and there are also credits which function as the platform’s designated digital currency. Users can deposit (= buy) credits using “real” money. As things stand, there is no withdrawal functionality but in principle it ought to exist.  

I have created three accounts to demonstrate the app’s cyber security vulnerabilities. The credentials are `admin / admin`, `cyrus_bertie / b3rtie1sB3st` and `beatrice_curry / YumCurry`. The latter two are the “main characters” but feel free to use the admin credentials to access the admin panel where all data can be tinkered with. Cyrus Bertie is our cybercriminal whereas Beatrice Curry is an innocent entrepreneur looking to fix bicycles. To get started, I recommend logging in as Cyrus and perhaps having a look around the site before going through the flaws in order. Just run `python manage.py runserver` and navigate to http://127.0.0.1:8000/abilityhub. The flaws represent four different risks from the [2021 edition of OWASP top 10](https://owasp.org/Top10/) plus CSRF.  

To avoid confusion, please note that Abilityhub uses a model called `Person` to refer to users and from here on out the term “person” shall be used in this text, too. Additionally, it shall be pointed out that there is an auxiliary django app called `chamberofsecrets`. All the necessary instructions for using the chamber are included in the flaw descriptions. 


## FLAW 1: CSRF 

[1] [bad credit form in `send.html`](abilityhub/templates/abilityhub/send.html#L25)

[2] [bad `SendView`](abilityhub/views.py#L298)

[3] [`|safe` in `myprofile.html`](abilityhub/templates/abilityhub/myprofile.html#L53)

[4] [`|safe` in `otherprofile.html`](abilityhub/templates/abilityhub/otherprofile.html#L57)  

[5] [malicious description](chamberofsecrets/STORAGE/csrf_description.html#L1)  

[6] [`SendForm` for the fix](abilityhub/forms.py#L56)

[7]* [`get()` serving the bad version](abilityhub/views.py#L124)

CSRF is facilitated by a weak form for sending credits to another user. Follow [1] to find the form in `send.html`, the template that gets rendered when one clicks “Send credits” in another person’s profile. The hidden field `from` is set to be `auth_person.pk`** and the person sending credits determines `credits`. Follow [2] and you will find `SendView` having a method decorator that exempts the view from CSRF protection.  

`myprofile.html` and `otherprofile.html` are the templates used for profile pages, the choice depending on if the profile to be viewed is one’s own or someone else’s. Both have a vulnerability in using `|safe` flag for the profile description, pointed by [3] and [4]. By default, any HTML input in django template variables is escaped (ie. converted into text) but `|safe` marks a variable as not requiring escaping. Cyrus can exploit this. As Cyrus, edit your description to be [5]. Since there is no CSRF protection, this form can send a `POST` request mimicking `send.html`’s form. You can test the scam by logging in as Beatrice. 

Many steps can be taken to fix and prevent this. At [1], L26-28 shall be replaced by L30-48 which include django’s `{% csrf_token %}` and the usage of django’s built-in form system (see [6] for `SendForm`). Alongside that change, At [2], the whole `SendView` starting from L296 shall be replaced by the better `SendView` starting from L356. Notice the latter lacking the CSRF exemption and using django’s form system. Finally, `|safe` shall be removed from [3] and [4].  

*This function serves the bad version of `send.html` and becomes redundant after the fixes. See comments in the code for details. 

**`auth_person` is set by abilityhub/utils/context_processors.py. Basically, all templates can access the authorized person’s model. 


## FLAW 2: XSS scripting (OWASP A03:2021-Injection) 

[1] [`|safe` in `messages.html`](abilityhub/templates/abilityhub/messages.html#L35)

[2] [malicious injection message](chamberofsecrets/STORAGE/injection_message.html#L1)

`messages.html` is the template for the messaging platform. As already described in FLAW 1, `|safe` causes any HTML code in the input to be used as HTML code instead of being converted into text. Therefore, at [1] it is not a good idea to include it when messages sent by users are rendered. 

Log in as Cyrus. In your messages, you will find a message sent by Beatrice. Cyrus considers this annoying spam and decides to steal Beatrice’s cookie. From [2] you will find a script that can be sent to Beatrice. 

Now, if you log in as Beatrice and navigate to your chat with Cyrus, injection will take place and Beatrice’s `document.cookie` gets stolen. To see a list of cookies stolen by this script, go to http://127.0.0.1:8000/chamberofsecrets/cookies/. 

Fixing this flaw is very simple: remove `|safe` from [1]. 


## FLAW 3: Broken access control (OWASP A01:2021-Broken Access Control) 

[1] ["My profile" in navigation bar](abilityhub/templates/abilityhub/navbar.html#L52)

[2] [`showMyProfile` in `urls.py`](abilityhub/urls.py#L11)

[3] [`showMyProfile` in `views.py`](abilityhub/views.py#L103) 

[4] [`ProfileView`](abilityhub/views.py#L107)

[5] [`setImagePrivacy` in `views.py`](abilityhub/views.py#L135)

[6] [`deleteImage` in `views.py`](abilityhub/views.py#L142)

[7] [`UploadView`](abilityhub/views.py#L161)

[8] [`DescriptionView`](abilityhub/views.py#L293)

What separates templates `myprofile.html` and `otherprofile.html` is that the former gives control to edit the accessed profile’s description and images. Naturally, this should only be possible for the person whose own profile is in question. Sources [1]-[4] demonstrate how this access control is implemented.

In the navigation bar at [1], there is a button “My profile” that uses `auth_person.id`.  This button points to [2] and calls [3] which sets a crucial boolean value in session to `True` and redirects to [4]. [4] uses `get_template_names()` to retrieve the boolean from session and determines that `myprofile.html` is the template to be rendered. 

The idea is that `myprofile.html` for each person can only be accessed via the navigation bar’s “My profile” button. However, this is not true. Say you are Cyrus again and you want to make Beatrice’s life miserable for spamming your inbox. Looking at the network traffic from his browser’s web developer tools while clicking “My profile”, Cyrus sees that his browser sends a `GET` request to `/abilityhub/3/myprofile/` before he ends up at `/abilityhub/3/profile/`. Cyrus can simply enter `/abilityhub/4/myprofile/` to his address bar to access Beatrice’s profile as if he was Beatrice.  

The fix includes three steps. First, `get_template_names()` in [4] shall be replaced with L109. Second, `myprofile.html` and `otherprofile.html` shall be replaced with just one template: `profile.html`. There is nothing to do here as you can find this template ready-made among the others. Third, [1], [5], [6], [7] and [8] shall have `abilityhub:profile` instead of `abilityhub:myprofile`. As can be seen, this is a simple but effective solution. Access control is now handled by `profile.html` which is basically the combination of codes from `myprofile.html` and `otherprofile.html`. `profile.html` gets the job done by comparing the person whose profile is accessed with `auth_person`. Since `auth_person` is set by a context processor, it cannot be faked by an attacker. 

After these fixes, lines pointed by [2] and [3] are redundant. 


## FLAW 4: Weak passwords are permitted (OWASP A07:2021-Identification and Authentication Failures) 

[1] [`RegisterView`](abilityhub/views.py#L53)

[2] [`AUTH_PASSWORD_VALIDATORS` in `settings.py`](csbp1/settings.py#L92)

As you may have noticed, the admin and Beatrice have weak passwords. Currently the app allows any password. 

[1] points to `RegisterView` where password requirements can be activated by uncommenting the commented lines. Everything here uses django’s built-in code. Two functions are called: `password_validators_help_texts()` and `validate_password()`. What these functions have in common is that, since they are both called without arguments, behind the scenes they call `get_default_password_validators()` which in turn calls `get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)`*. `AUTH_PASSWORD_VALIDATORS` are found at [2] and for this project the defaults have not been altered. The applied requirements are described to the user by the help texts added to the context for `register.html`. Said requirements are then enforced by `validate_password()` which throws a `ValidationError` if necessary. 

*As shown by django’s source code on GitHub 


## FLAW 5: Insufficient logging (OWASP A09:2021-Security Logging and Monitoring Failures) 

[1] [bad logging configuration](csbp1/settings.py#L169)

[2] [code for logging depositing errors](abilityhub/views.py#L259)

[3] [logging configuration selection](csbp1/settings.py#L246)

[4] [good logging configuration](csbp1/settings.py#L205)

[5] [`LoginView`](abilityhub/views.py#L30)  

[6] [url config for `LoginView`](abilityhub/urls.py#L7)

[7] [good `SendView`](abilityhub/views.py#L356)

[1] points to `LOGGING_BAD`, a logging configuration that is insufficient due to only storing logs locally to `csbp1/logs/logs.json`. Another problem with the current state of logging is its scope. The original `views.py` only has logging for depositing errors, the code for which is found at [2]. There definitely should be logging also for failed login attempts and transactions. 

The problem of only storing logs locally is fixed by switching `LOGGING_BAD` to `LOGGING_GOOD`. Simply change the commenting at [3] to achieve this. `LOGGING_GOOD`, found at [4], is equal to its predecessor except that it also has a handler for saving logs to the database.

The problem of limited scope is fixed in `views.py` and `urls.py`. For failed logins, two additions are needed. [5] extends django’s built-in `LoginView` to include logging and [6] puts the extension in use. When it comes to transactions, the issue was already fixed with FLAW 1 as the better `SendView` at [7] has logging included. 
