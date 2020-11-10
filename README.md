# BlackBoard Course Downloader

[![GitHub issues](https://img.shields.io/github/issues/TimEnglart/BlackBoard-Course-Downloader.svg?label=Issues)](https://github.com/TimEnglart/BlackBoard-Course-Downloader/issues)
[![GitHub stars](https://img.shields.io/github/stars/TimEnglart/BlackBoard-Course-Downloader.svg?color=Gold&label=Stars)](https://github.com/TimEnglart/BlackBoard-Course-Downloader/stargazers)

Python script to navigate a Black Board Learn sites API.

Currently only supports basic Black Board Course, Content and Attachment navigation

---

## Features

- Download Course Content

---

## Setup

##### Using Source (All Commands are Executed in the Command Line or Terminal)

1. [Clone](https://github.com/TimEnglart/BlackBoard-Course-Downloader.git) this repository.
2. Have [Python 3](https://www.python.org/downloads/) installed
3. Install required modules using `pip install -r requirements.txt` or `python -m pip install -r requirements.txt`
4. Navigate to downloaded repository and run command `python main.py`

---

## Launch Arguments

```
-v, --version           Displays Application Version                            Default: False
-g, --gui               Use GUI instead of CLI                                  Default: False              (Not Implemented)
-m, --mass-download     Download All Course Documents                           Default: False
-u, --username          Username to Login With                                  Default: None
-p, --password          Password to Login With                                  Default: None
-s, --site              Base Website Where Institute Black Board is Located     Default: None
-l, --location          Local Path To Save Content                              Default: './'
-c, --course            Course ID to Download                                   Default: None
-r, --record            Create A Manifest For Downloaded Data                   Default: True
-b, --backup            Keep Local Copy of Outdated Files                       Default: False
-V, --verbose           Print Program Runtime Information                       Default: False              (Not Implemented)
-C, --config            Location of Configuration File                          Default: './config.json'
-i, --ignore-input      Ignore Input at Runtime                                 Default: False              (Not Implemented)
-t, --threaded          Allows For Mass Downloads to Run in Multiple Threads    Default: False
-n, --num-threads       Sets the Maximum Number of Threads to Download With     Default: 4                  (4 Concurrent Downloads)
```

---

## Using The Program

When you launch the program it will prompt you for your login credentials for your Institution:

1. The first prompt is your your username. This will be what you usually use to login to your account.
   (The square brackets indicate what will be placed in the field if left blank) > Input Username [ ]: < Enter Username Here >
2. The next prompt will be for your password. (This will not show input when you enter a character)
   > Input Password: < Enter Password Here >
3. The final login prompt will be for your Institutes base learn URL. If you are unsure about the URl enter 'c' to search
   for your institute.  
    > Enter Black Board Host Website [ [ ] or 'c' to Search ]:
4. If you are successfully logged in you will then be shown a list of courses to chose from.

   > Sample Output (Layout is still a work in progress) ![image](https://user-images.githubusercontent.com/41773768/59965568-3ffed400-9553-11e9-83f1-6e307861744d.png)

   By entering a number shown within the square brackets the program will then attempt to get the given course data
   from either the Rest API (or BlackBoardMobile API). This will then output a new selection asking whether you want
   to get the child contents of the course or download all attachments within the course

   > Sample Output (Layout is still a work in progress) ![image](https://user-images.githubusercontent.com/41773768/59965641-493c7080-9554-11e9-8169-0a73bf2a2a19.png)

   1. If `Get Content` is selected the console will output a sub-selection of the child elements of the course

      > ![image](https://user-images.githubusercontent.com/41773768/59965729-4e4def80-9555-11e9-8632-c0bc45763884.png)

      When a child element is selected the console will clear and show all of the child elements of the course (similar
      to the the child content output)

      > ![image](https://user-images.githubusercontent.com/41773768/59965758-bc92b200-9555-11e9-8654-14dd7fdfd0eb.png)

      1. Selecting `Get Child Attachments` will output a sub-selection similar to the previous menu
         listing all possible child elements to access (Will show error message and navigate back if not child content is
         found)
      2. Selecting `Get Attachments` will output a sub-selection of all possible attached files to download.

         > ![image](https://user-images.githubusercontent.com/41773768/59965821-683c0200-9556-11e9-8cee-afa21970353f.png)

         When an attachment is selected the console will once again clear and show two options:

         1. `Download` which will download the attachment then navigate back to the parent element
         2. `Back` which will just go back to the parent element
            > ![image](https://user-images.githubusercontent.com/41773768/59965858-ce288980-9556-11e9-8add-7f96e0d09ae8.png)

   2. If `Download All Content` is selected the program will then iterate through all the elements of the course and
      its children and download all attachments (while Emulating the Blackboard Folder Structure) and print the filename
      when the download of that file is finished

---

## License

> Full license [here](https://github.com/TimEnglart/BlackBoard-Course-Downloader/blob/master/LICENSE)

This project is licensed under the terms of the **MIT** license.
