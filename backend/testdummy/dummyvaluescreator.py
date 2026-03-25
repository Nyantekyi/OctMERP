import random
import string
import django
from django.conf import settings
import random
import datetime
import secrets


def generate_secure_pin(length=5):
    return ''.join(secrets.choice('0123456789') for _ in range(length))

def generate_random_email():
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=15))
    domain = random.choice(["gmail.com", "yahoo.com", "hotmail.com"])
    return f"{random_str}@{domain}"


# email= generate_email()
# print(email)


def generate_random_names():
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=15))
    return f"{random_str}-test"


# names = generate_names()
# print(names)


def generate_random_date():
    today = datetime.date.today()
    random_days = random.randint(
        0, 365
    )  # Generate a random number of days between 0 and 365
    generated_date = today + datetime.timedelta(days=random_days)
    return generated_date


def generate_random_date_man():
    today = datetime.date.today()
    random_days = random.randint(
        0, 365
    )  # Generate a random number of days between 0 and 365
    generated_date = today - datetime.timedelta(days=random_days)
    return generated_date


# random_date = generate_random_date()
# print(random_date)


def generate_random_datetime(end_time=None):
    start_time = datetime.datetime.now()

    if end_time is None:
        end_time = start_time + datetime.timedelta(
            days=365
        )  # Set a default end time of 1 year from start time

    time_diff = end_time - start_time
    random_time_diff = random.randint(0, int(time_diff.total_seconds()))

    random_datetime = start_time + datetime.timedelta(seconds=random_time_diff)
    return random_datetime


# start_time = datetime.datetime.now()
# end_time = start_time + datetime.timedelta(days=7)
# random_datetime = generate_random_datetime(end_time)
# print(random_datetime)
def generate_random_integer(start, end):
    return random.randint(start, end)


# generate_random_integer(1, 10)


def generate_random_selection(items):
    if not items:
        return None
    return random.choice(items)


# fruits = ['apple', 'banana', 'orange', 'mango']
# random_fruit = generate_random_selection(fruits)
# print(random_fruit)


def generate_random_decimal(start, end, precision=2):
    factor = 10**precision
    return round(random.uniform(start, end), precision)


# start_value = 0.0
# end_value = 100.0
# precision_value = 2

# random_decimal = generate_decimal(start_value, end_value, precision_value)
# print(random_decimal)


def generate_random_boolean():
    return random.choice([True, False])


# print(generate_random_boolean())


##########################################
##########################################
#############barcode######################
##########################################
##########################################
def generate_random_barcode(length=12):
    """
    Generates a random barcode of the specified length.
    Default length is 12 digits.
    """
    digits = "0123456789"
    barcode = ""
    for _ in range(length):
        barcode += random.choice(digits)
    return barcode


# Generate a random barcode
# barcode = generate_barcode()

##########################################
##########################################
#############qr code######################
##########################################
##########################################
import string
import qrcode


def generate_random_qrcode():
    # Generate random data (e.g., alphanumeric string)
    random_data = "".join(random.choices(string.ascii_letters + string.digits, k=10))

    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # Add data to the QR code
    qr.add_data(random_data)
    qr.make(fit=True)

    # Create an image from the QR code
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Save the image as a PNG file
    image_filename = f"qrcode_{random_data}.png"
    qr_image.save(image_filename)

    return image_filename


# # Generate a random QR code
# random_qrcode = generate_random_qrcode()
# print(f"Generated QR code: {random_qrcode}")


def generate_qrcode(value):
    # Generate random data (e.g., alphanumeric string)
    random_data = str(value)

    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # Add data to the QR code
    qr.add_data(random_data)
    qr.make(fit=True)

    # Create an image from the QR code
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Save the image as a PNG file
    image_filename = f"qrcode_{random_data}.png"
    # qr_image.save(image_filename)

    return image_filename
