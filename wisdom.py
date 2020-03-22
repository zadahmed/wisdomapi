###########
# IMPORTS #
###########

import wptools
from flask import Flask, request, jsonify, render_template
from flask import session as login_session
import os
import wisdomaiengine
from urllib.parse import unquote
import pymongo
from bson import ObjectId
from bson.son import SON
from bson.code import Code
from io import BytesIO
import sys
from datetime import datetime
import base64
from PIL import Image
import numpy as np
import cv2
import requests
from passlib.apps import custom_app_context as pwd_context
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
from flask_mail import Mail, Message


##########################
# INSTANTIATE FLASK & DB #
##########################

app = Flask(__name__)
mail = Mail(app)
app.secret_key = "super secret key"
dir = os.path.abspath(os.path.dirname(__file__)) #  Directory
# user and pwd need to be environment variable os.environ["MONGO_DB_USER"]
user = "admin"
pwd = "admin123"
# connect to db
try:
    client = pymongo.MongoClient("mongodb://"+user+":"+pwd+"@localhost:27017/")
    db = client["wisdomdb"]
    print("connected to mongodb successfully!")
except:
    print("Unable to connect to database")
    sys.exit(1)
# instantiate collections
try:
    db_users = db["users"]
    db_bookmarks = db["bookmarks"]
    db_searches = db["searches"]
    db_search_terms = db["search_terms"]
    db_byod = db["byod"]
    db_highlights = db["highlights"]
    db_wikipedia = db["wikipedia"]
    db_summaries = db["summaries"]
    db_is_loggedin = db["is_loggedin"]
except:
    print("Unable to connect to collections")
    sys.exit(1)


#############
# FUNCTIONS #
#############

##########
# ROUTES #
##########

# landing page
@app.route('/', methods=['GET'])
def home():
    """
    Route for Wisdom web page.
    Web page to show users what Wisdom is, how it works, about
    the company and how they can download the app.
    """
    return render_template("index.html")


# privacy policy
@app.route("/privacy_policy", methods=["GET"])
def privacy_policy():
    "Temporary page for Privacy Policy"
    return render_template("privacy_policy.html")


# forgotten password
@app_route("/forgot_my_password", method=["GET"])
def forgot_my_password():



# sign up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Sign Up page.
    Contains form to sign up as a user on Wisdom platform.
    """
    if request.method == "GET":
        print("Hi")
    else:
        first_name = request.form['first_name']
        email = request.form['email']
        password = request.form['password']
        if first_name is None or email is None or password is None:
            msg = {"status" : { "type" : "fail" ,   "message" : "Missing fields"}}
            return jsonify(msg)
        user = db_users.find_one({"email": email})
        if user:
            msg = {"status" : { "type" : "fail" ,   "message" : "User already exists"}}
            return jsonify(msg)
        # hash password
        hashed_pw = pwd_context.hash(password)
        data = {"first_name": first_name,
                "email": email,
                "password": hashed_pw,
                "last_updated": datetime.utcnow()}
        search_id = db_users.insert(data, check_keys=False)
        # create user in logged in table
        data = {"user": str(search_id),
                "is_loggedin": False}
        is_loggedin = db_is_loggedin.insert(data, check_keys=False)
        #user.hash_password(password)
        msg = {"id": str(search_id)}
        print(msg)
        # send welcome email
        email = Message("Welcome!",
                        sender="support@wisdomai.co.uk",
                        recipients=email)
        email.html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html style="width:100%;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;padding:0;Margin:0;"><head><meta charset="UTF-8"><meta content="width=device-width, initial-scale=1" name="viewport"><meta name="x-apple-disable-message-reformatting"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta content="telephone=no" name="format-detection"><title>New email template 2020-03-22</title> <!--[if (mso 16)]><style type="text/css">     a {text-decoration: none;}     </style><![endif]--> <!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--> <!--[if !mso]><!-- --><link href="https://fonts.googleapis.com/css?family=Lato:400,400i,700,700i" rel="stylesheet"> <!--<![endif]--><style type="text/css">
@media only screen and (max-width:600px) {p, ul li, ol li, a { font-size:16px!important; line-height:150%!important } h1 { font-size:30px!important; text-align:center; line-height:120%!important } h2 { font-size:26px!important; text-align:center; line-height:120%!important } h3 { font-size:20px!important; text-align:center; line-height:120%!important } h1 a { font-size:30px!important } h2 a { font-size:26px!important } h3 a { font-size:20px!important } .es-menu td a { font-size:16px!important } .es-header-body p, .es-header-body ul li, .es-header-body ol li, .es-header-body a { font-size:16px!important } .es-footer-body p, .es-footer-body ul li, .es-footer-body ol li, .es-footer-body a { font-size:16px!important } .es-infoblock p, .es-infoblock ul li, .es-infoblock ol li, .es-infoblock a { font-size:12px!important } *[class="gmail-fix"] { display:none!important } .es-m-txt-c, .es-m-txt-c h1, .es-m-txt-c h2, .es-m-txt-c h3 { 
text-align:center!important } .es-m-txt-r, .es-m-txt-r h1, .es-m-txt-r h2, .es-m-txt-r h3 { text-align:right!important } .es-m-txt-l, .es-m-txt-l h1, .es-m-txt-l h2, .es-m-txt-l h3 { text-align:left!important } .es-m-txt-r img, .es-m-txt-c img, .es-m-txt-l img { display:inline!important } .es-button-border { display:block!important } a.es-button { font-size:20px!important; display:block!important; border-width:15px 25px 15px 25px!important } .es-btn-fw { border-width:10px 0px!important; text-align:center!important } .es-adaptive table, .es-btn-fw, .es-btn-fw-brdr, .es-left, .es-right { width:100%!important } .es-content table, .es-header table, .es-footer table, .es-content, .es-footer, .es-header { width:100%!important; max-width:600px!important } .es-adapt-td { display:block!important; width:100%!important } .adapt-img { width:100%!important; height:auto!important } .es-m-p0 { padding:0px!important } .es-m-p0r { 
padding-right:0px!important } .es-m-p0l { padding-left:0px!important } .es-m-p0t { padding-top:0px!important } .es-m-p0b { padding-bottom:0!important } .es-m-p20b { padding-bottom:20px!important } .es-mobile-hidden, .es-hidden { display:none!important } .es-desk-hidden { display:table-row!important; width:auto!important; overflow:visible!important; float:none!important; max-height:inherit!important; line-height:inherit!important } .es-desk-menu-hidden { display:table-cell!important } table.es-table-not-adapt, .esd-block-html table { width:auto!important } table.es-social { display:inline-block!important } table.es-social td { display:inline-block!important } }#outlook a {	padding:0;}.ExternalClass {	width:100%;}.ExternalClass,.ExternalClass p,.ExternalClass span,.ExternalClass font,.ExternalClass td,.ExternalClass div {	line-height:100%;}.es-button 
{	mso-style-priority:100!important;	text-decoration:none!important;}a[x-apple-data-detectors] {	color:inherit!important;	text-decoration:none!important;	font-size:inherit!important;	font-family:inherit!important;	font-weight:inherit!important;	line-height:inherit!important;}.es-desk-hidden {	display:none;	float:left;	overflow:hidden;	width:0;	max-height:0;	line-height:0;	mso-hide:all;}</style></head><body style="width:100%;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;padding:0;Margin:0;"><div class="es-wrapper-color" style="background-color:#F4F4F4;"> <!--[if gte mso 9]><v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t"> <v:fill type="tile" color="#f4f4f4"></v:fill> </v:background><![endif]-->
<table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;padding:0;Margin:0;width:100%;height:100%;background-repeat:repeat;background-position:center top;"><tr class="gmail-fix" height="0" style="border-collapse:collapse;"><td style="padding:0;Margin:0;"><table width="600" cellspacing="0" cellpadding="0" border="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td cellpadding="0" cellspacing="0" border="0" style="padding:0;Margin:0;line-height:1px;min-width:600px;" height="0"><img src="https://esputnik.com/repository/applications/images/blank.gif" style="display:block;border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;max-height:0px;min-height:0px;min-width:600px;width:600px;" alt width="600" height="1">
</td></tr></table></td></tr><tr style="border-collapse:collapse;"><td valign="top" style="padding:0;Margin:0;"><table cellpadding="0" cellspacing="0" class="es-content" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;"><table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="Margin:0;padding-left:10px;padding-right:10px;padding-top:15px;padding-bottom:15px;"> <!--[if mso]><table width="580" cellpadding="0" cellspacing="0"><tr><td width="282" valign="top"><![endif]-->
<table class="es-left" cellspacing="0" cellpadding="0" align="left" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left;"><tr style="border-collapse:collapse;"><td width="282" align="left" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;display:none;"></td></tr></table></td></tr></table> <!--[if mso]></td><td width="20"></td><td width="278" valign="top"><![endif]--><table class="es-right" cellspacing="0" cellpadding="0" align="right" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right;"><tr style="border-collapse:collapse;"><td width="278" align="left" style="padding:0;Margin:0;">
<table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;display:none;"></td></tr></table></td></tr></table> <!--[if mso]></td></tr></table><![endif]--></td></tr></table></td></tr></table><table class="es-header" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;background-color:#FFA73B;background-repeat:repeat;background-position:center top;"><tr style="border-collapse:collapse;"><td align="center" bgcolor="#538ae4" style="padding:0;Margin:0;background-color:#538AE4;">
<table class="es-header-body" width="600" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;"><tr style="border-collapse:collapse;"><td align="left" style="Margin:0;padding-bottom:10px;padding-left:10px;padding-right:10px;padding-top:20px;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="580" valign="top" align="center" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;display:none;"></td></tr></table></td></tr></table></td></tr></table></td></tr></table>
<table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;"><td style="padding:0;Margin:0;background-color:#538AE4;" bgcolor="#538ae4" align="center"><table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="600" valign="top" align="center" style="padding:0;Margin:0;">
<table style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:separate;border-spacing:0px;background-color:#FFFFFF;border-radius:4px;" width="100%" cellspacing="0" cellpadding="0" bgcolor="#ffffff" role="presentation"><tr style="border-collapse:collapse;"><td align="center" style="Margin:0;padding-bottom:5px;padding-left:30px;padding-right:30px;padding-top:35px;"><h1 style="Margin:0;line-height:58px;mso-line-height-rule:exactly;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;font-size:48px;font-style:normal;font-weight:normal;color:#111111;">Welcome!</h1></td></tr><tr style="border-collapse:collapse;"><td bgcolor="#ffffff" align="center" style="Margin:0;padding-top:5px;padding-bottom:5px;padding-left:20px;padding-right:20px;font-size:0;">
<table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td style="padding:0;Margin:0px;border-bottom:1px solid #FFFFFF;background:rgba(0, 0, 0, 0) none repeat scroll 0% 0%;height:1px;width:100%;margin:0px;"></td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr></table><table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;">
<table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="600" valign="top" align="center" style="padding:0;Margin:0;"><table style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:separate;border-spacing:0px;border-radius:4px;background-color:#FFFFFF;" width="100%" cellspacing="0" cellpadding="0" bgcolor="#ffffff" role="presentation"><tr style="border-collapse:collapse;">
<td class="es-m-txt-l" bgcolor="#ffffff" align="left" style="Margin:0;padding-top:20px;padding-bottom:20px;padding-left:30px;padding-right:30px;"><p style="Margin:0;-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-size:18px;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;line-height:27px;color:#666666;">We're so excited for your pursuit of Wisdom!<br><br>We want to build the best possible learning experience for you, so please let us know what you think of our app by leaving feedback!<br><br>Let us know if you have any questions or problems by emailing <a target="_blank" href="" style="-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;font-size:18px;text-decoration:underline;color:#FFA73B;">support@wisdomai.co.uk </a>- we're always here to help out.<br><br>Thanks,<br>
The Wisdom Team <br><br>Follow us!<br>LinkedIn: <a target="_blank" href="" style="-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;font-size:18px;text-decoration:underline;color:#FFA73B;">linkedin.com/company/wisdom-ai-tech</a><br>Instagram: @wisdom_ai<br>Facebook: /wisdom.ai.ltd<br></p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;">
<table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="600" valign="top" align="center" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td align="center" style="Margin:0;padding-top:10px;padding-bottom:20px;padding-left:20px;padding-right:20px;font-size:0;">
<table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td style="padding:0;Margin:0px;border-bottom:1px solid #F4F4F4;background:rgba(0, 0, 0, 0) none repeat scroll 0% 0%;height:1px;width:100%;margin:0px;"></td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr></table><table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;">
<table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="600" valign="top" align="center" style="padding:0;Margin:0;"><table style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:separate;border-spacing:0px;background-color:#FFECD1;border-radius:4px;" width="100%" cellspacing="0" cellpadding="0" bgcolor="#ffecd1"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;display:none;"></td></tr></table></td></tr></table></td></tr></table></td></tr></table>
<table cellpadding="0" cellspacing="0" class="es-footer" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;background-color:transparent;background-repeat:repeat;background-position:center top;"><tr style="border-collapse:collapse;"><td align="center" style="padding:0;Margin:0;"><table class="es-footer-body" width="600" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;"><tr style="border-collapse:collapse;"><td align="left" style="Margin:0;padding-top:30px;padding-bottom:30px;padding-left:30px;padding-right:30px;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;">
<td width="540" valign="top" align="center" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td align="left" style="padding:0;Margin:0;padding-top:25px;"><p style="Margin:0;-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-size:14px;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;line-height:21px;color:#666666;">Wisdom AI Ltd<br>20-22 Wenlock Road<br>London<br>N1 7GU</p></td></tr></table></td></tr></table></td></tr></table></td></tr></table><table class="es-content" cellspacing="0" cellpadding="0" align="center" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;table-layout:fixed !important;width:100%;"><tr style="border-collapse:collapse;">
<td align="center" style="padding:0;Margin:0;"><table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;" width="600" cellspacing="0" cellpadding="0" align="center"><tr style="border-collapse:collapse;"><td align="left" style="Margin:0;padding-left:20px;padding-right:20px;padding-top:30px;padding-bottom:30px;"><table width="100%" cellspacing="0" cellpadding="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;"><td width="560" valign="top" align="center" style="padding:0;Margin:0;"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;"><tr style="border-collapse:collapse;">
<td class="es-infoblock made_with" align="center" style="padding:0;Margin:0;line-height:120%;font-size:0;color:#CCCCCC;"><a target="_blank" href="https://viewstripo.email/?utm_source=templates&utm_medium=email&utm_campaign=software2&utm_content=trigger_newsletter" style="-webkit-text-size-adjust:none;-ms-text-size-adjust:none;mso-line-height-rule:exactly;font-family:lato, 'helvetica neue', helvetica, arial, sans-serif;font-size:12px;text-decoration:underline;color:#CCCCCC;"><img src="https://edrcee.stripocdn.email/content/guids/CABINET_9df86e5b6c53dd0319931e2447ed854b/images/64951510234941531.png" alt width="125" style="display:block;border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;"></a></td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr></table></div></body>
</html>"""
        mail.send(email)
        return jsonify(msg)


# log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Log In page.
    Contains form to log in to an existing users profile.
    """
    if request.method == "GET":
        print("hi")
    else:
        # get details from form
        email = request.form['email']
        password = request.form['password']
        user = db_users.find_one({"email": email})
        # if uyser doesn't exist
        if not user:
            msg = {"status" : { "type" : "fail" ,   "message" : "User does not exist, please sign up"}}
            return jsonify(msg)
        stored_pw = user.get("password")
        # if credentials are wrong
        if not pwd_context.verify(password, stored_pw):
            msg = {"status" : { "type" : "fail" ,   "message" : "Invalid password, try again"}}
            return jsonify(msg)
        first_name = user.get("first_name")
        profile_id = user.get("_id")
        # set is_loggedin = True if login details are correct
        is_loggedin = db_is_loggedin.find_one({"user": str(profile_id)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == False:
                data = {"is_loggedin": True}
                db_is_loggedin.update({"user": str(profile_id)}, {"$set": data})
                msg = {"id": str(profile_id)}
                return jsonify(msg)
            else:
                msg = {"id": str(profile_id)}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "fail" ,   "message" : "User not found, please sign up"}}
            return jsonify(msg)


# log out
@app.route('/logout/<string:userid>')
def logout(userid):
    """
    Log Out route.
    Log the user out of their Wisdom account and clear the
    session cookie stored.
    """
    if userid:
        is_loggedin = db_is_loggedin.find_one({"user": str(userid)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == True:
                data = {"is_loggedin": False}
                db_is_loggedin.update({"user": str(userid)}, {"$set": data})
                msg = {"status" : { "type" : "success" ,   "message" : "Logged out"}}
                return jsonify(msg)
            else:
                msg = {"status" : { "type" : "fail" ,   "message" : "Already logged out"}}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "fail" ,   "message" : "User not found, sign up"}}
            return jsonify(msg)
    else:
        msg = {"status" : { "type" : "fail" ,   "message" : "Provide userid"}}
        return jsonify(msg)


########
# APIs #
########

# log out
@app.route('/logincheck/<string:userid>')
def logincheck(userid):
    """
    Check whether user is logged in.
    """
    if userid:
        is_loggedin = db_is_loggedin.find_one({"user": str(userid)})
        if is_loggedin:
            if is_loggedin.get("is_loggedin") == True:
                msg = {'id':str(userid)}
                return jsonify(msg)
            else:
                msg = {"status" : { "type" : "fail" ,   "message" : "User is logged out"}}
                return jsonify(msg)
        else:
            msg = {"status" : { "type" : "fail" ,   "message" : "User not found, sign up"}}
            return jsonify(msg)
    else:
        msg = {"status" : { "type" : "fail" ,   "message" : "Provide userid"}}
        return jsonify(msg)


# factual
@app.route('/definition/<string:category>/<string:search_me>/<string:userid>', methods=['GET'])
def definitionsearch(category, search_me, userid):
    """
    Factual search.
    Returns factual definitions of the search term.
    """
    user_id = userid
    search_me = search_me.strip()
    # get wikipedia
    try:
        # see if it is saved in db
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        if search_term and search_term.get("category") == category:
            search_id = search_term.get("_id")
            wiki = db_wikipedia.find_one({"search_id": search_id})
            if wiki:
                wiki_def = wiki.get('wiki_summary')
        # else use wikipedia API
        else:
            wiki_def = wisdomaiengine.factualsearch(category, search_me.lower())
    except:
        wiki_def = "Oops"
    # check if search_term has been run before
    results = db_search_terms.find_one({"value": search_me.lower()})
    if results and results.get("category") == category:
        search_id = results.get('_id')
    else:
        data = {"value": search_me.lower(), "category": category}
        search_id = db_search_terms.insert(data, check_keys=False)
    # write data to searches collection
    data = {"search_id": search_id,
            "category": category,
            "user": userid,
            "datetime": datetime.utcnow()}
    x = db_searches.insert(data, check_keys=False)
    # save data to wikipedia collection
    wiki = db_wikipedia.find_one({"search_id": search_id})
    if wiki:
        if wiki.get("wiki_summary") != wiki_def:
            data = {"search_id": search_id,
                    "wiki_summary": wiki_def,
                    "datetime": datetime.utcnow()}
            db_wikipedia.update({"search_id": search_id}, {"$set": data})
    else:
        data = {"search_id": search_id,
                "wiki_summary": wiki_def, 
                "datetime": datetime.utcnow()}
        x = db_wikipedia.insert(data, check_keys=False)
    # return json
    jsonob = jsonify(search=search_me,
                    factual=wiki_def)
    return jsonob


    
# research papers
@app.route('/research/<string:category>/<string:search_me>/<string:userid>', methods=['GET'])
def papersearch(category, search_me, userid):
    """
    Research paper search.
    Returns research papers of the search term.
    """

    user_id = userid
    search_me = search_me.strip()
    research_papers = {}
    all_papers = []
    # get arxiv results
    try:
        papers = wisdomaiengine.getarxivresults(search_me.lower())
        for paper in papers:
            all_papers.append(paper[1])
        research_papers["arxiv"] = papers
    except:
        research_papers["arxiv"] = ""
    # get google scholar results
    try:
        google_scholar = wisdomaiengine.getgooglescholar(search_me.lower())
        research_papers["google scholar"] = google_scholar
        for paper in google_scholar:
            all_papers.append(paper[-1])
    except:
        research_papers["google scholar"] = ""
    # get DOAJ articles
    try:
        doaj = wisdomaiengine.getdoajarticles(search_me.lower())
        research_papers["DOAJ"] = doaj
        for article in doaj:
            all_papers.append(article[2])
    except:
        research_papers["DOAJ"] = ""
    # get wordcloud of all papers
    try:
        all_papers_text = " ".join(a for a in all_papers)
        wordcloud = wisdomaiengine.wordcloud(search_me, all_papers_text)
    except:
        wordcloud = "No topics found!..."
    # return json object
    jsonob = jsonify(papers=research_papers,
                        wordcloud=wordcloud)
    return jsonob



# wisdom engine
@app.route('/wisdom/<string:search_me>/<string:source>/<path:pdfurl>/<string:userid>', methods=["GET"])
def wisdom(search_me, source, pdfurl, userid):
    """
    Wisdom AI engine.
    This extracts insights from documents and returns key points,
    abstracts, wordclouds and PDF viewer if possible.
    """
    ### source needs to be name of data source ("arxiv", "google scholar", "doaj")
    search_me = search_me.strip()
    # check if pdfurl has been found before
    pdf = db_summaries.find_one({"url": pdfurl})
    if pdf:
        text = pdf.get('text')
        summary = pdf.get('summary')
        topics = pdf.get('topics')
        # update in db if data is 1 days or older
        last_updated = datetime.utcnow() - pdf.get("last_updated")
        last_updated_diff = last_updated.days
        if last_updated_diff > 1:
            search_term = db_search_terms.find_one({"value": search_me.lower()})
            search_id = search_term.get("_id")
            data = {"search_id": search_id,
                    "url": pdfurl, "source": source, "text": text,
                    "summary": summary, "topics": topics, "last_updated": datetime.utcnow()}
            db_summaries.update({"url": pdfurl}, {"$set": data})
        else:
            pass
    else:
        text = wisdomaiengine.pdfdocumentextracter(pdfurl)
        summary = wisdomaiengine.summarisepdfdocument(text)
        topics = wisdomaiengine.wordcloud(search_me, text)
        if topics is None:
            topics = ['No Topics Found']
        # write data to arxiv collection
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        search_id = search_term.get("_id")
        data = {"search_id": search_id,
                "url": pdfurl,
                "source": source,
                "text": text,
                "summary": summary,
                "topics": topics,
                "last_updated": datetime.utcnow()}
        x = db_summaries.insert(data, check_keys=False)
    # return json
    summaryjson = jsonify(wisdomtopics=topics, wisdomsummary=summary)
    return summaryjson



# bring your own document
@app.route('/byod/<string:content_type>', methods=['GET' , 'POST'])
def byod(content_type):
    """
    Bring Your Own Document.
    Make use of the Wisdom AI engine on your own
    documents. Upload an image from your gallery, take
    a picture or supply a webpage.
    """
    if request.method == "GET":
        print("Hi")
    else:
        user_id = request.form['userid']
        if content_type == "gallery":
            data = request.form['image']
            name = request.form['name']
            nparr = np.fromstring(base64.b64decode(data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            text = wisdomaiengine.bringyourowndocument(img)
            key_points = wisdomaiengine.summarisetext(text)
            key_points = "\n\n".join(k for k in key_points)
            save = {"user": user_id,
                    "content_type": content_type,
                    "doc_name": name,
                    "text": text,
                    "key_points": key_points,
                    "datetime_uploaded": datetime.utcnow()}
            x = db_byod.insert(save, check_keys=False)
            jsonob = jsonify(text=text,
                             key_points=key_points)
            return jsonob
        if content_type == "camera":
            data = request.form['image']
            name = request.form['name']
            nparr = np.fromstring(base64.b64decode(data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            text = wisdomaiengine.bringyourowndocument(img)
            key_points = wisdomaiengine.summarisetext(text)
            key_points = "\n\n".join(k for k in key_points)
            save = {"user": user_id,
                    "content_type": content_type,
                    "doc_name": name,
                    "text": text,
                    "key_points": key_points,
                    "datetime_uploaded": datetime.utcnow()}
            x = db_byod.insert(save, check_keys=False)
            jsonob = jsonify(text=text,
                             key_points=key_points)
            return jsonob
        if content_type == "webpage":
            page = request.form['data']
            name = request.form['name']
            r = requests.get(page)
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')
            #soup = BeautifulSoup(html, 'lxml')
            body = soup.body
            if body:
                # remove footer
                while body.footer:
                    soup.footer.decompose()
                # remove scripts
                while body.script:
                    soup.script.decompose()
                # get p tags
                main_body = body.find_all(["p"])
                text = ""
                for m in main_body:
                    text += m.get_text()+" "
                text = text.strip()
                key_points = wisdomaiengine.summarisetext(text)
                key_points = "\n\n".join(k for k in key_points)
                save = {"user": user_id,
                        "content_type": content_type,
                        "doc_name": name,
                        "text": text,
                        "key_points": key_points,
                        "datetime_uploaded": datetime.utcnow()}
                x = db_byod.insert(save, check_keys=False)
                jsonob = jsonify(text=text,
                                 key_points=key_points)
            else:
                msg = {"text":"No text found, please try another website"}
                jsonob = jsonify(msg)
        return jsonob


# highlighter
@app.route('/highlight/<string:search_me>/<string:word>/<string:userid>', methods=["GET"])
def highlight(search_me, word, userid):
    """
    Wisdom highlighting insights.
    When user highlights a word on the Wisdom screen,
    this route will provide a definition of that word.
    """
    if db_is_loggedin.find_one({"user": userid}).get("is_loggedin") == True:
        word = word.strip()
        results = wisdomaiengine.highlighter(word)
        search_term = db_search_terms.find_one({"value": search_me.lower()})
        search_id = search_term.get("_id")
        data = {"user": userid,
                "search_id": search_id,
                "highlighted_word": word,
                "results": results,
                "date_saved": datetime.utcnow()}
        x = db_highlights.insert(data, check_keys=False)
        jsonob = jsonify(results=results)
        return jsonob
    else:
        msg = {"status" : { "type" : "fail" ,   "message" : "Please log in"}}
        return jsonify(msg)


# bookmark content
@app.route("/bookmark/<string:search_me>/<string:source>/<path:url>", methods=["POST"])
def bookmark(search_me, source, url):
    """
    Bookmarker.
    This route is used to save documents to a user
    profile, so that they can revisit it easily.
    """
    user_id = request.form['userid']
    search_term = db_search_terms.find_one({"value": search_me.lower()})
    search_id = search_term.get("_id")
    data = {"user": user_id,
            "search_id": search_id,
            "source": source,
            "url": url, 
            "date_saved": datetime.utcnow()}
    x = db_bookmarks.insert(data, check_keys=False)
    msg = {"status" : { "type" : "success" ,   "message" : "Bookmark created"}}
    return jsonify(msg)



# profile page
@app.route('/profile/<string:userid>', methods=["GET"])
def profile(userid):
    """
    Profile page.
    This route will return all stored information
    within Wisdom that the user needs when logging
    into the application.
    """
    # get bookmarked content
    bookmarks = db_bookmarks.find({"user": userid})
    bookmarks = [{"search_term": db_search_terms.find_one({"_id": b["search_id"]}).get("value"), "source": b["source"], "url": b["url"], "date_saved": b["date_saved"].strftime("%H:%M %B %d, %Y")} for b in bookmarks]
    # get previous searches
    searches = db_searches.find({"user": userid})
    searches = [{"search_term": db_search_terms.find_one({"_id": s["search_id"]}).get("value"), "category": s["category"], "datetime": s["datetime"].strftime("%H:%M %B %d, %Y")} for s in searches]
    # get byod
    byod = db_byod.find({"user": userid})
    byod = [{"content_type": b["content_type"], "doc_name": b["doc_name"], "text": b["text"], "key_points": b["key_points"], "datetime_uploaded": b["datetime_uploaded"].strftime("%H:%M %B %d, %Y")} for b in byod]
    # get highlightds
    # highlights = db_highlights.find({"user": userid})
    # highlights = [{"search_term": db_search_terms.find_one({"_id": h["search_id"]}).get("value"), "highlighted_word": h["highlighted_word"], "results": h["results"], "date_saved": h["date_saved"].strftime("%H:%M %B %d, %Y")} for h in highlights]
    jsonob = jsonify(bookmarks=bookmarks,
                     searches=searches,
                     byod=byod)
    return jsonob


# top 10 searches
@app.route('/wisdom/top_n/<string:userid>', methods=["GET"])
def top_n(userid):
    """
    Top N
    This API returns the top N searches by count
    from the Wisdom community.
    """
    agg = [s["search_id"] for s in db_searches.find()]
    table = pd.DataFrame()
    table["searches"] = Counter(agg).keys()
    table["count"] = Counter(agg).values()
    table = table.sort_values("count", ascending=False)
    table = table[:10]
    search_ids = table["searches"].values
    counts = table["count"].values
    n = 0
    top_n = []
    while n < len(search_ids):
        top_n.append([str(db_search_terms.find_one({"_id": search_ids[n]}).get("value")), str(counts[n])])
        n += 1
    jsonob = jsonify(top_n=top_n)
    return jsonob

                                                                            
# run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=5000)
