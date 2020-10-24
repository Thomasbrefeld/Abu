from PIL import Image, ImageFont, ImageDraw, ImageFile
from io import BytesIO
import requests
import colorsys
import logging
import random
import ctypes
import praw
import sys
import os

img_load = 'img/image_current.jpg'
img_dflt = 'img/image_default.jpg'
img_next = 'img/image_next.jpg'

subreddits = 'conf/subreddits.txt'
proir_image_log = 'logs/proir_image.txt'

logging.basicConfig(filename = 'logs/errors.log', level = logging.DEBUG, format='%(asctime)s %(levelname)s = %(name)s: %(message)s')

src = os.path.dirname(os.path.realpath(__file__))

class Images:
    screen_size = 1920, 1080

    def __init__(self, img, url, title, sub, score):
        self.img = img
        self.url = url
        self.title = title
        self.sub = sub
        self.score = score

        self.log()
        self.write()
        
        self.img.save(img_next)

    def log(self):
        try:
            logging.info("2. Logging proir image url")
            print("2. Logging proir image url")
            file = open(proir_image_log, 'a+')
            file.write(str(self.url) + "\n")
        except Exception as err:
            logging.critical("File saving failed: " + str(img_next) +  ", Aborting program. ERROR: " + str(err))
            sys.exit()

    def color_freq(self):
        logging.info("Finding most frequent color in image")
        print("Finding most frequent color in image")
        width, height = self.img.size
        pixels = self.img.getcolors(width * height)

        frequency = pixels[0]
        for count, pixel in pixels:
            if (count > frequency[0]):
                frequency = count, pixel
        
        return frequency

    def clean_text(self, text):
        logging.info("Cleaning text input")
        print("Cleaning text input")
        text = str(text)
        if (len(text) > 40):
            text = ('%.40s' % text) + ". . ."
        return text

    def image_text(self, img, input_text, ft_size, x, y, color):
        logging.info("Adding text to image")
        print("Adding text to image")
        input_text = self.clean_text(input_text)
        font = ImageFont.truetype("arial.ttf", size = int(ft_size))
        draw = ImageDraw.Draw(img)
        location = int(x), int(y)
        draw.text(location, str(input_text), font = font, fill = color)

    def write(self):
        try:
            logging.info("3. Coinverting picture to screen size and adding text")
            print("3. Coinverting picture to screen size and adding text")
            self.img = self.img.convert("RGB")
            self.img.show() #1
            primary_color = self.color_freq()
            

            if (sum(primary_color[1]) / len(primary_color[1]) > 127):
                logging.info('Text color set: dark')
                print('Text color set: dark')
                text_color = 63, 63, 63
            else:
                logging.info('Text color set: light')
                print('Text color set: light')
                text_color = 191, 191, 191

            self.img.thumbnail(self.screen_size)
            width, height = self.img.size
            bkg_img = (Image.new(mode = "RGB", size = self.screen_size, color = primary_color[1]))
            bkg_img.show() #2
            bkg_img.paste(self.img, (int(self.screen_size[0]/2-width/2), int(self.screen_size[1]/2-height/2)))
            bkg_img.show() #4
            self.img = bkg_img

            self.image_text(self.img, self.title, 16, 20, 20, text_color)
            self.image_text(self.img, self.sub, 12, 20, 40, text_color)
            self.image_text(self.img, self.score, 11, 20, 56, text_color)
            self.img.show() #5
        except Exception as err:
            logging.critical("Failed to generate image: Aborting program. ERROR: " + str(err))


def reddit(list_sub, log_list, max_recursion, reddit_call_limit = 1):
    try:
        client_id = 'Xx2UtG87diFDDQ'
        client_secret = 'bMk1mOQIBiX7uCKe2NpWUeq2C-U'
        user_agent = 'Abu v6'

        reddit_pull = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        ran_num = random.randrange(0, len(list_sub))

        valid_sub = []
        top_score = -1

        for sub in reddit_pull.subreddit(list_sub[ran_num].replace('\n', '')).top('week', limit=reddit_call_limit):
            if (not(sub.stickied)):
                if (not(sub.over_18)):
                    if (not((sub.url + '\n') in log_list)):
                        if (sub.url.endswith('.jpg')):
                            valid_sub.append((sub.url, sub.score, sub.title, sub.subreddit))

        logging.info("Reddit call limit:" + str(reddit_call_limit))
        print("Reddit call limit:" + str(reddit_call_limit))
        if not valid_sub:
            if(reddit_call_limit >= pow(2, max_recursion)):
                raise Exception("No valid pictures within the recsion limit.")
            return reddit(list_sub, log_list, max_recursion, reddit_call_limit * 2)

        logging.info("Picture found")
        print("Picture found")
        for x in valid_sub:
            if (x[1] > top_score):
                top_score = x[1]

        for url, score, title, found_sr in valid_sub:
            if(score == top_score):
                r = requests.get(url)
                if r.status_code == 200:
                    Images(Image.open(BytesIO(r.content)),url, title, found_sr, score)
                    return
    except Exception as err:
        logging.critical("Reddit update failed: Aborting program.\n ERROR: " + str(err))
        sys.exit()
                

def load(f_name):
    try:
        load_list = []
        file = open(str(f_name), 'r')
        for line in file:
            load_list.append(line)
        file.close()
        logging.info("File named: " + str(f_name) +  " successfully opened.")
        print("File named: " + str(f_name) +  " successfully opened.")
        return load_list
    except IOError:
        open(str(f_name), 'w')
        logging.warning("File named: " + str(f_name) +  " not found. Creating file.")
        load(f_name)
    except Exception as err:
        logging.critical("File creation failed: " + str(f_name) +  ", Aborting program. ERROR: " + str(err))
        sys.exit()

def update(img):
    try:
        try:
            logging.info("Updating current image")
            print("Updating current image")
            if (os.path.exists(img)):
                os.remove(img)
            if (os.path.exists(img_next)):
                os.rename(img_next, img)
        except Exception as err:
            logging.critical("Failed to update next. ERROR: " + str(err))
        if(os.path.exists(img)):
            ctypes.windll.user32.SystemParametersInfoW(20, 0, (src + '/' + img), 0x2)
            logging.info("Background: " + str(img) +  " successfully opened.")
        else:
            raise Exception("Path does not exist.")
    except Exception as err:
        if(img == img_dflt):
            logging.critical("Background update failed: " + str(img) +  ", Aborting program.\n ERROR: " + str(err))
            sys.exit()
        else:
            logging.warning("Background update failed: " + str(img) +  ", Loading Default.\n ERROR: " + str(err))
            update(img_dflt)

if __name__ == "__main__":
    try:
        logging.info("0. Program Starting")
        print("0. Program Starting")
        update(img_load)
        logging.info("1. Finding image:")
        print("1. Finding image:")
        reddit(load(subreddits), load(proir_image_log), 10)
        logging.info("4. Program Finished - program exiting")
        print("4. Program Finished - program exiting")
    except Exception as err:
        logging.critical("Program Failed. ERROR: " + str(err))