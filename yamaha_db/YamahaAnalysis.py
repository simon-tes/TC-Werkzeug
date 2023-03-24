
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os

from YamahaDatabase import YamahaTraceability
#

class Analysis:
    """class to access Yamaha Database
    """
    def __init__(self, path_database: str) -> None:
        """init function

        Args:
            path_database (str): path to Database
        """
        self.path_database = path_database
        self.database = None
        self.connected = False

    def connect_to_database(self) -> None:
        """opens a connection to the database
        """
        self.database = YamahaTraceability(self.path_database)
        self.connected = self.database.connect_to_database()

    def is_connected(self) -> bool:
        """returns True if database is open

        Returns:
            bool: True or False
        """
        return self.connected

    def close_connection(self) -> None:
        """close the database
        """
        self.database.close_connection()
        self.connected = False

    def get_all(self, table: str) -> list:
        """get all entrys from a given table

        Args:
            table (str): name of the table

        Returns:
            list: all content of this table
        """
        query = "SELECT * FROM " + table
        #return self.database.execute_read_query(query)
        return pd.read_sql_query(query, self.database.connection)

    def get_many(self, table: str, number: int) -> list:
        """get x items from a given table

        Args:
            table (str): name of the table
            number (int): how many rows

        Returns:
            list: x items of this table
        """
        query = "SELECT * FROM " + table
        return self.database.execute_read_many(query, number)
        
    def get_specific(self, table: str, column: str, value: str) -> list:
        """get specific rows from a given table

        Args:
            table (str): name of the table
            column (str): name of the column in which the search value stands
            value (str): search value

        Returns:
            list: all items that match as pandas dataframe
        """
        query = "SELECT * FROM " + table + " WHERE " + column + " = '" + value + "'"
        return pd.read_sql_query(query, self.database.connection)
        #return self.database.execute_read_query(query)

    def get_2_specific(self, table: str, column: tuple, value: tuple) -> list:
        """get specific rows from a given table

        Args:
            table (str): name of the table
            column (tuple): name of the columns in which the search values stands
            value (tuple): search values

        Returns:
            list: all items that match as pandas dataframe
        """
        query = "SELECT * FROM " + table + " WHERE " + column[0] + " = '" + value[0] + \
                                            "' AND " + column[1] + " = '" + value[1] + "'"
        return pd.read_sql_query(query, self.database.connection)
        #return self.database.execute_read_query(query)

    def get_range(self, table: str, column: str, lower: str, higher: str) -> list:
        """get rows from a given table which values ar between lower and higher

        Args:
            table (str): name of the table
            column (str): name of the column in which the search value stands
            lower (str): lower value
            higher (str): higher value

        Returns:
            list: all items that match as pandas dataframe
        """

        query = "SELECT * FROM " + table + " WHERE " + column + \
                " >= " + lower + " AND " + column + " <= " + higher
        #return self.database.execute_read_query(query)
        return pd.read_sql_query(query, self.database.connection)


if __name__ == "__main__":
    test = 3

    path_database = "D:/Yamaha DB/Yamaha Trace-DB.db"
    database = Analysis(path_database)
    database.connect_to_database()
    if database.connected == False:
        print("[ERROR] unable to connect to database.")
        exit()

    if test == 0:
        print(database.get_info("lotLog", "operatorId", "Fischer M."))
        
    elif test == 1:
        data = database.get_range("lotLog", "dateTime", "20220101000000", "202212300000000")
        data = data[data.producedBoard >= 2]

        data["dateTime"] = pd.to_datetime(data["dateTime"])
        data = data.sort_values("dateTime", ascending=True)


        data.groupby(data["dateTime"].dt.isocalendar().week)["workingRatio"].mean().plot()
        #plt.title("mean working ratio per week")
        plt.xlabel("week")
        plt.ylabel("working ratio (%)")
        #plt.xticks(rotation=90)
        #plt.grid(True)
        #plt.subplots_adjust(left=0.125, bottom=0.125, right=0.95, top=0.93)
        plt.savefig('working ratio.png', dpi=300, bbox_inches='tight')
        plt.show()

        data.groupby(data["dateTime"].dt.isocalendar().week)["partsConsumption"].sum().plot()
        plt.xlabel("week")
        plt.ylabel("total parts (pcs)")
        plt.savefig('total parts per week.png', dpi=300, bbox_inches='tight')
        plt.show()

        data.groupby(data["dateTime"].dt.isocalendar().day)["partsConsumption"].mean().plot()
        plt.xlabel("day")
        plt.ylabel("mean parts (pcs)")
        plt.savefig('parts mean per day.png', dpi=300, bbox_inches='tight')
        plt.show()

        data.groupby(data["dateTime"].dt.isocalendar().week)["mountRate"].mean().plot()
        plt.xlabel("week")
        plt.ylabel("mount rate (%)")
        plt.savefig('mount rate.png', dpi=300, bbox_inches='tight')
        plt.show()

        data.groupby(data["dateTime"].dt.isocalendar().week)["operatorCallTime"].mean().plot()
        plt.xlabel("week")
        plt.ylabel("mean operator call time (s)")
        plt.savefig('mean operator call time.png', dpi=300, bbox_inches='tight')
        plt.show()


    elif test == 2:
        data = np.array(database.get_many("lotLog", 10))

    elif test == 3:
        data = database.get_2_specific("pcbMountLog", ("recipeId" , "silk"), ("0349A", "C512"))
        data["dateTime"] = pd.to_datetime(data["dateTime"])

        #data = data[(data["dateTime"] > pd.Timestamp("20210801000000") & 
        #             data["dateTime"] > pd.Timestamp("20211001000000"))]

        filename = "test"
        user = os.getlogin()
        path = os.path.join("\\\\elfab.local/FolderRedirection/", user, "Desktop", filename + ".xlsx")
        data.to_excel(path)

    elif test == 4:
        data = database.get_2_specific("pcbMountLog", ("recipeId" , "recipeId"), ("0486A", "0486B"))
        data["dateTime"] = pd.to_datetime(data["dateTime"])

        filename = "test"
        user = os.getlogin()
        path = os.path.join("\\\\elfab.local/FolderRedirection/", user, "Desktop", filename + ".xlsx")
        data.to_excel(path)

    elif test == 10:
        data = database.get_range("programLog_mounter", "key", "20211001-1", "20211101-1")
        data["programDate"] = pd.to_datetime(data["programDate"])

        filename = "test1"
        user = os.getlogin()
        path = os.path.join("\\\\elfab.local/FolderRedirection/", user, "Desktop", filename + ".xlsx")
        data.to_excel(path)

    elif test == 11:
        data = database.get_range("programLog_mounter", "key", "20211001-1", "20211101-1")
        data["programDate"] = pd.to_datetime(data["programDate"])

        filename = "test1"
        user = os.getlogin()
        path = os.path.join("\\\\elfab.local/FolderRedirection/", user, "Desktop", filename + ".xlsx")
        data.to_excel(path)

    elif test == 100:
        df = database.get_range("lotLog", "dateTime", "20220328000000", "202204030000000")

        #df.to_excel("bevor.xlsx")

        df1 = df.drop_duplicates().groupby("recipeId", sort=False, as_index=False)["pickUpErrorCounter"].sum()

        #df1.to_excel("after.xlsx")


        sns.set_theme(style="whitegrid")
        g = sns.barplot(x="recipeId", y="pickUpErrorCounter", data=df1, color="blue")
        g.bar_label(g.containers[0])
        plt.show()

        """fig = px.bar(df1, x="recipeId", y="pickUpErrorCounter")
        fig.show()"""



    
    else:
        pass
    
    database.close_connection()
    