BlackBoard Course Downloader
=======
[![GitHub release](https://img.shields.io/github/release/TimEnglart/BlackBoard-Course-Downloader.svg?label=Latest%20Release)](https://github.com/TimEnglart/BlackBoard-Course-Downloader/releases)
[![GitHub issues](https://img.shields.io/github/issues/TimEnglart/BlackBoard-Course-Downloader.svg?label=Issues)](https://github.com/TimEnglart/BlackBoard-Course-Downloader/issues)
[![GitHub stars](https://img.shields.io/github/stars/TimEnglart/BlackBoard-Course-Downloader.svg?color=Gold&label=Stars)](https://github.com/TimEnglart/BlackBoard-Course-Downloader/stargazers)

Python script to navigate a Black Board Learn sites API.

Currently only supports basic Black Board Course, Content and Attachment navigation

---

## Features
- Download Course Content

---

## Setup
##### Using Source
1. [Clone](https://github.com/TimEnglart/BlackBoard-Course-Downloader.git) this repository.
2. Have Python 3 installed
3. Install required modules using `pip install -r requirements.txt` or `python -m pip install -r requirements.txt`
4. Navigate to downloaded repository and run command `python main.py`
##### Using Release (Windows Only)
1. [Download the Latest Release](https://github.com/TimEnglart/BlackBoard-Course-Downloader/releases)
2. Run downloaded executable
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
-r, --record            Create A Manifest For Downloaded Data                   Default: True               (Not Implemented)
-V, --verbose           Print Program Runtime Information                       Default: False              (Not Implemented)
-C, --config            Location of Configuration File                          Default: './config.json'    
-i, --ignore-input      Ignore Input at Runtime                                 Default: False              (Not Implemented)
```

---

## License
>Full license [here](https://github.com/TimEnglart/BlackBoard-Course-Downloader/blob/master/LICENSE)

This project is licensed under the terms of the **MIT** license.