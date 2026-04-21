# pybots
## Simple python bots for social media like LinkedIn


## What are these small bots
There is a number of companies making money by selling bots that make friendships, send spam etc. These bots do the same for free if you can follow the manual. Worth to mention, that these bots are testing from a non-paying account.  
I have no intentions in showing good programming practices here. These are quick and dirty scripts put together to do simple things. Don't hate me for it. I never claimed to be a good Python dev.  
Who am I? Check out my website at https://www.uldiskarlovskarlovskis.com/  




## Ubuntu support
### First setup
sudo apt install python3 python3-pip
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo snap remove chromium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb


### reuse setup
source venv/bin/activate
python3 <scipt.py> [parameters]

e.g.
python3 LinkedIn_ind_connect_company.py




## How to use these small bots on windows conda:
1. create a file named creds.txt with your username on the 1st line and password on the 2nd in the folder outside of the current directory - ../creds.txt  
2. setup Python. Anaconda is a nice wrapper, rather heavy though. Here's commands you can reuse:  
conda env list  
conda create -n py310  
conda activate py310  
conda install python=3.10  
conda install -c anaconda numpy  
conda install -c anaconda pandas  
conda install -c conda-forge matplotlib  
conda install -c conda-forge notebook  
jupyter notebook  
conda install -c conda-forge selenium  


### Now you are ready to execute the scripts with "python <script>"
1. just make sure the commandline is running from the repo folder. 
2. My example:
cd C:/uld/git/pybots
conda activate py310
python LinkedIn_ind_connect_company.py


## Troubleshooting
1. If it throws error about wrong variable type, override latest selenium with "pip install selenium==4.9.0"  

2. if you face an issue that Chrome broswer opens and then times out without hitting any URLs, you're likely having the weird "snap" issue. Try this:

3. if you have VS Code installed, just hit "code ."

4. the "python3 launch_browser.py" will open an empty browser. There you can do what you need to see how it works. Should work from VS Code as well.
