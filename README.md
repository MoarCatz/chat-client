[![Build Status](https://travis-ci.org/MoarCatz/chat.svg?branch=master)](https://travis-ci.org/MoarCatz/chat)

## Chat

This is a simple encrypted chat application with a desktop client.

### Features

- **Requests** :question::
Adding a user sends him a request with an optional message. The user can accept it, after which you can chat, or decline it, which hides you from new requests. You can take the request back before it gets accepted or declined. 
- **Blacklist** :no_entry_sign::
You can add people to the blacklist. Those people can't send you messages or requests and view your profile.
- **Profile info** :information_source::
After registration you can edit your profile's info in the menu or by pressing your name in the chat.
- **Sending format** :envelope::
Messages will be packed with the timestamp and sender into a JSON string with the delimiter ",", not ", ". 
- **Session IDs** :id::
A session ID is created on login/register and mapped to a username. It is formed by a concatenation of the IP address, from where the request came and the username, mapped to that ID, thrown into a MD5 hash function. A session is terminated when a user logs out. After that, the session record is removed from active sessions. The record includes a username, a session ID and an IP address from where the request came. 
In the implementation, also concatenate last N chars of the timestamp to alter session IDs. Probably, N = 3
- **Usernames** :bust_in_silhouette::
Usernames consist of alphanumeric characters and underscores. They should be between 2 and 15 in length. Validation of a username should take place on both sides, as we can't be sure that the request is made by our application. 
- **Message search** :mag::
You can search for messages that contain certain text or search for all messages in a certain dialog in a given period of time (two timepoints). Matching uses the SQL's BETWEEN operator like so:
```
SELECT * FROM d{} WHERE timestamp BETWEEN val1 AND val2
```
  To avoid a lot of work, but as a potential in the future, make a way to locate a found by text message in a dialog. 
  Implementation (naive): 
```
msg = SELECT rowid WHERE content...
SELECT * FROM d{} WHERE rowid BETWEEN msg - 5 AND msg + 5
```
Won't work because SQLite doesn't guarantee any row order.
- **Encryption** :lock::
All clients know the server's public key. When a new session is added, a client's public key encrypted with the server's public key is sent to the server. Response with the session ID and other responses to this session are now encrypted with the client's public key
- **Message length** :speech_balloon::
Messages are limited to 1000 characters.

### Contribution

Any of your suggestions would be appreciated. Will be happy to receive any PRs.

### Our goals

Building an app with complete server and data encryption.
