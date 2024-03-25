# pybots
## Simple python bots for social media like LinkedIn


There is a number of companies making money by selling bots that make friendships, send spam etc. These bots do the same for free if you can follow the manual. Worth to mention, that these bots are testing from a non-paying account.  
I have no intentions in showing good programming practices here. These are quick and dirty scripts put together to do simple things. Don't hate me for it. I never claimed to be a good Python dev.  
Who am I? Check out my website at https://www.uldiskarlovskarlovskis.com/  


## How to use these small bots:
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


### Now you are ready to execute the scripts with "python <script>", just make sure the commandline is running from the repo folder. My example:
cd C:/uld/pybots  
conda activate py310  
python LinkedIn_ind_invite_company.py  


## Troubleshooting
If it throws error about wrong variable type, override latest selenium with "pip install selenium==4.9.0"  



