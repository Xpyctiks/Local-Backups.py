# Local-Backups
This is a simple python script which makes few types of backups:  
- MySQL databases backup  
- Folders backup  
Those backups are divided by types to:  
- LocalServerBackups - makes backups of DB and Folder of local server.  
- OtherBackups - makes backups of any other files and databases - may be not important for current server, but must be on the server too.  

Sends information and alerts via Telegram bot if TG bot credentials are set.  
Logs all actions to the local log file.   

Installation:  
- Just clone the script to any folder. For example, on Debian-based OS it could be /opt/ folder with script's subfolder.
- Launch for the first time with any of parameter and config. file will be created:  
    <script_name> Daily-Local  - do daily backups of databases for local server only - \"LocalServerBackups\" part of the config file.  
    <script_name> Weekly-Local - do weekly backups of databases and folders for local server only - \"LocalServerBackups\" part of the config file.  
    <script_name> Daily-Other  - do daily backups of any other databases - \"OtherBackups\" part of the config file.  
    <script_name> Weekly-Other - do weekly backups of databases and folders for any others - \"OtherBackups\" part of the config file.  
- Then you need to edit the config file and set some variables:  
  - "telegramToken" and "telegramChat" - if you want to receive notification to Telegram  
  - "logFolder" - where to store log files. Name of every log files is current date without time.  
  - "backupFolder" - where to store backups. It is the root folder for local and other backup actions.  
  - "dailyFolder" and "weeklyFolder" - folders to store daily and weekly backups for Local server only.  
  - "DefaultDb*" - set of default parameters for access to MySQL database.Are used when no local values set in config file.Socket has higher priority to use in case it is set with Port at the same time.  
  - "LocalServerBackups" - part where you can set folders and databases for Local server backups. For example /etc/, /opt/, and so on.  
  - "OtherBackups" - part where you can set any other folders and databases. For example some sites in /var/www and their databases.  
- In personal configuratoion blocks every value of Name is used for backup file name or db dump file name.  
- Using key "DB" or "Folder" you are setting the type of backup.  
- For type "DB" can be additionally set personal values of "User","Host","Port","Socket","Password".  
- For all databases backup you can type for the key "DB" one of values: "ALL" or "FETCH". If "ALL" value is set - all databases in one file backups will be created. If "FETCH" - every database will be dumped as single one. But that function requires root access to make the script able to see all databases.  
- Also if you launch any of DB backup from 0 to 12 hours (24h time) - the DB backup will contain "-morning" prefix. IF you launch the script again after 12:00 - another dump will be created with "-evening" prefix. That allows to make to copies of DB if you need.  
