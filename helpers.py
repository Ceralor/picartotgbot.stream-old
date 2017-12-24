def get_mysql_cursor(mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    return (conn,cursor)
def mysql_fetch_assoc(cursor):
	data = cursor.fetchall()
	column_names = [x[0] for x in cursor.description]
	assoc_data = [dict(zip(column_names,x)) for x in data]
	return assoc_data
