# This is not part of the actual server

Messages:
Text | Timestamp * 100 | Sender

Requests:
From | To | Message

Users:
0 Name PRIMARY KEY | 1 PasswordHash | 2 Friends | 3 Favorites | 4 Blacklist | 5 Dialogs
Profiles:
0 Name FOREIGN KEY | 1 Status | 2 Email | 3 Birthday | 4 About | 5 Image

Sessions:
Name | SessionID | IP
