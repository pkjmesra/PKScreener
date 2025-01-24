"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
try:
    import libsql_client as libsql
except: # pragma: no cover
    pass
import pyotp
from time import sleep

from PKDevTools.classes.log import default_logger
from pkscreener.classes.ConfigManager import tools, parser

class PKUser:
    userid=0
    username=""
    name=""
    email=""
    mobile=0
    passkey=""
    totptoken=""
    licensekey=""
    lastotp=""

    def userFromDBRecord(row):
        user = PKUser()
        user.userid= row[0]
        user.username= row[1]
        user.name= row[2]
        user.email= row[3]
        user.mobile= row[4]
        user.passkey= row[5]
        user.totptoken= row[6]
        user.licensekey= row[7]
        user.lastotp= row[8]
        return user

class DBManager:
    configManager = tools()
    configManager.getConfig(parser)
    
    def __init__(self):
        from dotenv import dotenv_values
        try:
            local_secrets = dotenv_values(".env.dev")
            self.url = local_secrets["TDU"]
            self.token = local_secrets["TAT"]
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            self.url = None
            self.token = None
        self.conn = None
    
    def shouldSkipLoading(self):
        skipLoading = False
        try:
            import libsql_client as libsql
        except: # pragma: no cover
            skipLoading = True
            pass
        return skipLoading
    
    def connection(self):
        try:
            if self.conn is None:
                # self.conn = libsql.connect("pkscreener.db", sync_url=self.url, auth_token=self.token)
                # self.conn.sync()
                self.conn = libsql.create_client_sync(self.url,auth_token=self.token)
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return self.conn

    def validateOTP(self,userIDOrName,otp):
        try:
            otpValue = 0
            dbUsers = self.getUserByIDorUsername(userIDOrName)
            token = ""
            if len(dbUsers) > 0:
                token = dbUsers[0].totptoken
                lastOTP = dbUsers[0].lastotp
                if token is not None:
                    otpValue = str(pyotp.TOTP(token,interval=int(DBManager.configManager.otpInterval)).now())
            else:
                print(f"Could not locate user: {userIDOrName}")
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        isValid = (otpValue == str(otp)) and int(otpValue) > 0
        if not isValid and len(token) > 0:
            isValid = pyotp.TOTP(token,interval=int(DBManager.configManager.otpInterval)).verify(otp=otp,valid_window=60)
            default_logger().debug(f"User entered OTP: {otp} did not match machine generated OTP: {otpValue} while the DB OTP was: {lastOTP} with local config interval:{DBManager.configManager.otpInterval}")
            if not isValid and len(str(lastOTP)) > 0 and len(str(otp)) > 0:
                isValid = (str(otp) == str(lastOTP)) or (int(otp) == int(lastOTP))
        return isValid

    def getOTP(self,userID,username,name,retry=False):
        try:
            otpValue = 0
            dbUsers = self.getUserByID(int(userID))
            if not retry:
                if len(dbUsers) > 0:
                    token = dbUsers[0].totptoken
                    if token is not None:
                        otpValue = str(pyotp.TOTP(token,interval=int(DBManager.configManager.otpInterval)).now())
                    else:
                        # Update user
                        user = PKUser.userFromDBRecord([userID,username.lower(),name,dbUsers[0].email,dbUsers[0].mobile,dbUsers[0].passkey,pyotp.random_base32(),dbUsers[0].licensekey,dbUsers[0].lastotp])
                        self.updateUser(user)
                        return self.getOTP(userID,username,name,retry=True)
                else:
                    # Insert user
                    user = PKUser.userFromDBRecord([userID,username.lower(),name,None,None,None,pyotp.random_base32(),None,None])
                    self.insertUser(user)
                    return self.getOTP(userID,username,name,retry=True)
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        try:
            self.updateOTP(userID,otpValue)
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        return otpValue

    def getUserByID(self,userID):
        try:
            users = []
            cursor = self.connection() #.cursor()
            records = cursor.execute(f"SELECT * FROM users WHERE userid={self.sanitisedIntValue(userID)}") #.fetchall()
            for row in records.rows:
                users.append(PKUser.userFromDBRecord(row))
            # cursor.close()
            if len(records.columns) > 0 and len(records.rows) <= 0:
                # Let's tell the user
                default_logger().debug(f"User: {userID} not found! Probably needs registration?")
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
        return users

    def getUserByIDorUsername(self,userIDOrusername):
        try:
            users = []
            cursor = self.connection() #.cursor()
            try:
                userID = int(userIDOrusername)
            except: # pragma: no cover
                userID = 0
                pass
            if userID == 0:
                records = cursor.execute(f"SELECT * FROM users WHERE username={self.sanitisedStrValue(userIDOrusername.lower())}") #.fetchall()
            else:
                records = cursor.execute(f"SELECT * FROM users WHERE userid={self.sanitisedIntValue(userID)}") #.fetchall()
            for row in records.rows:
                users.append(PKUser.userFromDBRecord(row))
            if len(records.columns) > 0 and len(records.rows) <= 0:
                # Let's tell the user
                default_logger().debug(f"User: {userIDOrusername} not found! Probably needs registration?")
                print(f"Could not locate user: {userIDOrusername}. Please reach out to the developer!")
                sleep(3)
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
        return users
    
    def insertUser(self,user:PKUser):
        try:
            result = self.connection().execute(f"INSERT INTO users(userid,username,name,email,mobile,passkey,totptoken,licensekey) VALUES ({self.sanitisedIntValue(user.userid)},{self.sanitisedStrValue(user.username.lower())},{self.sanitisedStrValue(user.name)},{self.sanitisedStrValue(user.email)},{self.sanitisedIntValue(user.mobile)},{self.sanitisedStrValue(user.passkey)},{self.sanitisedStrValue(user.totptoken)},{self.sanitisedStrValue(user.licensekey)});")
            if result.rows_affected > 0 and result.last_insert_rowid is not None:
                default_logger().debug(f"User: {user.userid} inserted as last row ID: {result.last_insert_rowid}!")
            # self.connection().commit()
            # self.connection().sync()
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
    
    def sanitisedStrValue(self,param):
        return "''" if param is None else f"'{param}'"

    def sanitisedIntValue(self,param):
        return param if param is not None else 0

    def updateUser(self,user:PKUser):
        try:
            result = self.connection().execute(f"UPDATE users SET username={self.sanitisedStrValue(user.username.lower())},name={self.sanitisedStrValue(user.name)},email={self.sanitisedStrValue(user.email)},mobile={self.sanitisedIntValue(user.mobile)},passkey={self.sanitisedStrValue(user.passkey)},totptoken={self.sanitisedStrValue(user.totptoken)},licensekey={self.sanitisedStrValue(user.licensekey)},lastotp={self.sanitisedStrValue(user.lastotp)} WHERE userid={self.sanitisedIntValue(user.userid)}")
            if result.rows_affected > 0:
                default_logger().debug(f"User: {user.userid} updated!")
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None

    def updateOTP(self,userID,otp):
        try:
            result = self.connection().execute(f"UPDATE users SET lastotp={self.sanitisedStrValue(otp)} WHERE userid={self.sanitisedIntValue(userID)}")
            if result.rows_affected > 0:
                default_logger().debug(f"User: {userID} updated with otp: {otp}!")
        except Exception as e: # pragma: no cover
            default_logger().debug(e, exc_info=True)
            pass
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None