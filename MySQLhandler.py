
# MySQLhandler.py
# Jeremy Albrecht
# 31/01/2016
# ajeremyalbrecht@gmail.com / @jeremyy_a

# Library to help handling the request to a DB, MySQL here, by creating Objet for each table
# The only thing you have to change here, is in the __init__ method, the value to connevt to your database and the name of your master table
# The first thing to do after modifying this file is to make an import statement
# Next you define the object like customers = MySQL('customers_table')
# And that's all ! You can use the method @add, @get, @remove, @modify, don't forget to @close at the end of your script
import pymysql
import pymysql.cursors
import re



class MySQL:

    def __init__(self, dbName):
        self.db = ''    #Contain DB Name
        self.dbInfo = {}    #Contain DB info such as name of fields, type of fields and if they can be null
        self.connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='Railchta2c',
                                     db='laravel',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor,
				     autocommit=True)
        with self.connection.cursor() as cursor:
            self.db = dbName
            db = self.db
            sql = "DESCRIBE `" + db + "`"   #Get data from DBD
            result = cursor.execute(sql)
            type = []   #Empty array to contain type of fields
            null = []   #Empty array to contain if they can be null
            name = []   #Empty array to contain fields name
            for iquery in range(0, result): #For each row
                data = cursor.fetchone()
                type.append(data['Type'])   #Append the type
                null.append(data['Null'])   #Append the null
                name.append(data['Field'])   #Append the name
            self.dbInfo[db] = {}
            self.dbInfo[db]['Type'] = type  #Update it to the dbInfo dict
            self.dbInfo[db]['Null'] = null  #Update it to the dbInfo dict
            self.dbInfo[db]['Name'] = name  #Update it to the dbInfo dict
        #Now handling the fields the user won't have to provide such as id, date of creation or date of modification
        self.dbInfo[db]['NonRequiredFields'] = []
        for element in self.dbInfo[db]['Name']:
            if element == "id" or element == "created_at" or element =="updated_at":
                self.dbInfo[db]['NonRequiredFields'].append(element)

    def testData(self, data):
        i = 0   #Counter to handle data fetching
        db = self.db
        dbInfo = self.dbInfo
        isValid = True  #bool that say if the data is valid
        if len(data) != (len(dbInfo[db]['Type']) - len(dbInfo[db]['NonRequiredFields'])):   #Checking if enough fields has been provided
            isValid = False #If not return error
            raise ValueError("You didn't provide the correct number of row.")
        #Validating data:
        for element in data:
            if re.match(r"^int\([0-9]{0,3}\)$", dbInfo[db]['Type'][i+1], flags=0):  #Field is an int, checking if user's data is
                try:
                    int(element)
                except ValueError:  #No !
                    isValid = False
                else:   #Yes !
                    isValid = isValid and True
            elif re.match(r"^float$", dbInfo[db]['Type'][i+1], flags=0):    #Field is a float, checking if user's data is
                try:
                    float(element)
                except ValueError:
                    isValid = False
                else:
                    isValid = isValid and True
            elif re.match(r"^text$", dbInfo[db]['Type'][i+1], flags=0): #Field is a text, no need to test
                isValid = isValid and True
            elif re.match(r"^date$", dbInfo[db]['Type'][i+1], flags=0): #Fields is a date, checking if user's data is
                if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', element):  #Yes !
                    isValid = isValid and True
                else:
                    isValid = False
            elif re.match(r"^varchar\([0-9]{0,3}\)$", dbInfo[db]['Type'][i+1], flags=0):    #Fields is a float, checking if user's data is
                length =  re.match(r"^varchar\(([0-9]{0,3})\)$", dbInfo[db]['Type'][i+1])
                if len(element) <= int(length.group(1)):    #Checking length
                    isValid = isValid and True
                else:
                    isValid = False
            elif re.match(r"^datetime$", dbInfo[db]['Type'][i+1], flags=0): #Fields is a datetime, checking if user's data is
                if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$', element):
                    isValid = isValid and True
                else:
                    isValid = False
            else:
                isValid = False
            i = i + 1   #Increment dbInfo->Type to choose
        return isValid
    def all(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM `" + self.db +"`"
                numberOfResult = cursor.execute(sql)
                if numberOfResult >= 1:
                    result = []
                    for j in range(0, numberOfResult):
                        result.append(cursor.fetchone())
                    return result
        except pymysql.err.InternalError as e:
            print(e)

    def add(self, data):
        #Add data to the DB
        db = self.db
        dbInfo = self.dbInfo
        #Handling the add to the DB
        if self.testData(data): #Is data ok ?
            try:
                with self.connection.cursor() as cursor:
                    dataSQL = ''.join([',\' %s\'' % x for x in data])   #Dynamic data
                    if 'created' in dbInfo[db]['NonRequiredFields']:    #If is created in table add it manually
                        if 'modified' in dbInfo[db]['NonRequiredFields']:   #If is modified in table add it manually
                            sql = "INSERT INTO `" + db + "` VALUES ('0'" + dataSQL + ", NOW(), NULL)"
                        else:
                            sql = "INSERT INTO `" + db + "` VALUES ('0'" + dataSQL + ", NOW())"
                    else:
                        sql = "INSERT INTO `" + db + "` VALUES ('0'" + dataSQL + ")"
                    cursor.execute(sql)
            except pymysql.err.InternalError as e:
                print("Unable to insert into DB. Please check configuration.")
                print(e)

    def get(self, FieldName, value):
        #Get data from a name field passed by name and the value of this field passed via value
        db = self.db
        dbInfo = self.dbInfo
        #Testing the value the user gave us
        if FieldName in dbInfo[db]['Name']:
            FieldIndex = dbInfo[db]['Name'].index(FieldName)
        #Checking if data provided by user match the type of data of the field
        isValid = True
        if re.match(r"^int\([0-9]{0,3}\)", dbInfo[db]['Type'][FieldIndex], flags=0):  #Field is an int, checking if user's data is
            try:
                int(value)
            except ValueError:  #No !
                isValid = False
            else:   #Yes !
                isValid = isValid and True
        elif re.match(r"^tinyint\([0-9]{0,3}\)$", dbInfo[db]['Type'][FieldIndex], flags=0):  #Field is an int, checking if user's data is
            try:
                int(value)
            except ValueError:  #No !
                isValid = False
            else:   #Yes !
                isValid = isValid and True
        elif re.match(r"^float$", dbInfo[db]['Type'][FieldIndex], flags=0):    #Field is a float, checking if user's data is
            try:
                float(value)
            except ValueError:
                isValid = False
            else:
                isValid = isValid and True
        elif re.match(r"^text$", dbInfo[db]['Type'][FieldIndex], flags=0): #Field is a text, no need to test
            isValid = isValid and True
        elif re.match(r"^date$", dbInfo[db]['Type'][FieldIndex], flags=0): #Fields is a date, checking if user's data is
            if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', value):  #Yes !
                isValid = isValid and True
            else:
                isValid = False
        elif re.match(r"^varchar\([0-9]{0,3}\)$", dbInfo[db]['Type'][FieldIndex], flags=0):    #Fields is a float, checking if user's data is
            length =  re.match(r"^varchar\(([0-9]{0,3})\)$", dbInfo[db]['Type'][FieldIndex])
            if len(value) <= int(length.group(1)):    #Checking length
                isValid = isValid and True
            else:
                isValid = False
        elif re.match(r"^datetime$", dbInfo[db]['Type'][FieldIndex], flags=0): #Fields is a datetime, checking if user's data is
            if re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$', value):
                isValid = isValid and True
            else:
                isValid = False
        else:
            isValid = False
        if isValid:
            try:
                with self.connection.cursor() as cursor:
                    sql = "SELECT * FROM `" + db + "` WHERE `" + FieldName + "`= %s"
                    numberOfResult = cursor.execute(sql, (value,))
                    if numberOfResult >= 1:
                        result = []
                        for j in range(0, numberOfResult):
                            result.append(cursor.fetchone())
                        return result
                    else:
                        return cursor.fetchone()
            except pymysql.err.InternalError as e:
                print(e)

    def remove(self, id):
        #Remove data by id
        db = self.db
        dbInfo = self.dbInfo

        isValid = False
        try:    #Check if data is an int
            int(id)
        except ValueError:  #No !
            isValid = False
        else:   #Yes !
            isValid = True
        #If data provided is good, remove entry !
        if isValid:
            try:
                with self.connection.cursor() as cursor:
                    sql = "DELETE FROM `" + db + "` WHERE `id`= %s"
                    cursor.execute(sql, (id,))
                    return cursor.fetchone()
            except pymysql.err.InternalError as e:
                print(e)

    def modify(self, idEntry, FieldName, value):
        #Modify data from an existing entry
        #Data provided by user should be an array, [0] is the field name to modify, [1] is the value modified
        db = self.db
        dbInfo = self.dbInfo
        #Handling it
        #Testing the value the user gave us
        if FieldName in dbInfo[db]['Name']:
            FieldIndex = dbInfo[db]['Name'].index(FieldName)
        #Checking if data provided by user match the type of data of the field
        isValid = True
        try:
            int(idEntry)
        except ValueError:
            isValid = False
        if isValid:
            try:
                with self.connection.cursor() as cursor:
                    sql = "UPDATE `" + db + "` SET `" + dbInfo[db]['Name'][FieldIndex] + "`= %s,`updated_at`=NOW() WHERE `id`= %s"
                    cursor.execute(sql, (value, idEntry))
                    return cursor.fetchone()
            except pymysql.err.InternalError as e:
                print(e)
        else:
            raise ValueError("You didn't provide the value matching the structure type of the table. Gimme good values and I'll help you !")

    def close(self):
        self.connection.close()
