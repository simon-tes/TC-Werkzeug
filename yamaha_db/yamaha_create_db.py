import pyodbc, os
import xml.etree.ElementTree as ET


def linear_contains(iterable, key):
    for item in iterable:
        if item[0] == key:
            return item[1]
    return False



dirname = os.path.abspath(r"\\192.168.102.10\Yamaha\Database\D_Base")
repl_lst = {" ": "", "\n": ""}

#connect to database 
conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\elfab.local\Shares\SMD\SMD-Bestdaten\3-Mdb\EFA.accdb;')

cursor = conn.cursor()
cursor.execute("SELECT * FROM Artikelstamm")
database = cursor.fetchall()

#open xml
filename = os.path.join(dirname, "database.fdx")
tree = ET.parse(filename)
root = tree.getroot()

total = 0
count = 0
new = 0
check = True
for part in root.iter("Part_001"):
    partname = part.get("PartsName")
    comment = part.get("Comment")
    total += 1
    if len(partname) == 14 and check == True:
        if partname[7] != "-":
            continue
        new_comment = linear_contains(database, partname)
        if new_comment == False:
            new_comment = input(f"{partname[-6:]} ")
            if new_comment == "":
                check = False
                continue

            for key, value in repl_lst.items():
                    new_comment = new_comment.replace(key, value)
            
            new_comment = new_comment.upper()

            cursor = conn.cursor()
            cursor.execute("""INSERT INTO Artikelstamm ([Artikelnummer], [Elfab-Bezeichnung]) VALUES (?, ?);""", (partname, new_comment))
            conn.commit()
            new += 1

        elif new_comment == comment:
            count += 1
            continue

        part.set("Comment", str(new_comment))
        count += 1

conn.close()
filename = os.path.join(dirname, "database.xml")
tree.write(filename)

print("file written", filename)
print(f"{count} from {total}, {new} are newly added")
