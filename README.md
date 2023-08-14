## Tools

1. Python  
2. MySQL

## ENV
python3 -m venv virtualenv
source virtualenv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt

## Database (Mysql inside WSL)
sudo service mysql start

# NOTE
I'm not using models neither to create the database nor to handle the endpoints. Why? I wanted to showcase that I know how to work pure SQL. To see, how I use flask models and marshmellow, please refer to this [project](https://github.com/ArmandoDLaRosa/booking-api)