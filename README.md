# what is the opposite of a sockpuppet?

It's blind: humans must control whose fingerprints are added into the keyring.  Manually.
There's magic and ceremony to it: the coven sets 2 passphrases in person, together, at a gathering.

The first is a session password, for initiation.  The second is a permanent phrase, which is the sentinel you use to request a 2FA token if needed.

The initiation rites are as follows: You "chat" that first phrase to the libpurple client.  If phrase matches, it'll try to sign your fingerprint.  The facilitator then compares your fingerprint, on your device, to what the libpurple client receives.  She accepts you; it signs your key.  You sign its key.  The facilitator then adds you to the communal account's following list on Twitter.

From then on, you may "chat" the libpurple client anything via any app that supports OTR and Jabber.  (Pidgin, Adium, Chatsecure...)

"Chat" the second, sentenel phrase, surrounded by `~*` and `*~` to request a 2FA token.  Otherwise, the libpurple client will funnel your message to the Twitter account.

#### A short spec:

1.	tornado + libpurple + cmd
1.	receives SMS from Twitter only on /twilio endpoint
1.	receives requests from libpurple client only on /purple endpoint
1.	hooked up to twitter API and can only post tweets on successfully authenticated ("verified") request from libpurple client
1.	Redis for managing temporary data (i.e. who's waiting to receive a 2fa chal response) using TTL
1.	app itself deploys in Docker; host machine has a shell to it (hope this is a good idea; have not prodded how Time works with this configuration!)

## API

#### Public API (exposed over HTTP):

1.	POST /twilio/chal_response

#### Private API (exposed over Redis pub-sub):

1.	coven_shell.introduce
1.	coven_purple_client.accept_member
1.	coven_purple_client.request_chal_response
1.	coven_purple_client.tweet_message

## Install

Make sure you have the following dependencies:

1.	python-dev
1.	pip
1.	virtualenv
1.	docker

Then,
	
	git submodule update --init --recursive
	./setup.sh

## Run

If install was successful, run `coven` in a terminal.

## Update

You should get into the habit of checking for updates to this codebase.  Do this by running:

	git pull origin master
	./update.sh

This script will push all changes to `src` to your image in Docker, which you can invoke by running `coven`