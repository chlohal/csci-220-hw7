import re
import os
import time
from urllib.parse import parse_qs
from html import escape

import psycopg2

VALID_COURSE_NUMBER_REGEX = re.compile(r"^\w{2,} \d{2,}$")
VALID_ROOM_NUMBER_REGEX = VALID_COURSE_NUMBER_REGEX

def wrapBody(body, title="Blank Title"):
    return (
        "<html>\n"
        "<head>\n"
        f"<title>{title}</title>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "<hr>\n"
        f"<p>This page was generated at {time.ctime()}.</p>\n"
        "</body>\n"
        "</html>\n"
    )

def showAllStudents(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM student")

    ## create an HTML table for output:
    body = """
    <a href="/">Back to Course List</a>
    <h2>Student List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1"><b>Student ID</b></font></td>
        <td><font size=+1"><b>Name</b></font></td>
        <td><font size=+1"><b>delete</b></font></td>
      </tr>
    """

    count = 0
    # each iteration of this loop creates on row of output:
    for student_id, student_name in cursor:
        body += (
            "<tr>"
            f"<td><a href='?action=get_student&student_id={student_id}'>{student_id}</a></td>"
            f"<td>{escape(student_name)}</td>"
            "<td><form method='post' action='/'>"
            f"<input type='hidden' NAME='student_id' VALUE='{student_id}'>"
            f"<input type='hidden' NAME='action' VALUE='delete_student'>"
            '<input type="submit" name="deleteStudent" value="Delete">'
            "</form></td>"
            "</tr>\n"
        )
        count += 1

    body += "</table>" f"<p>Found {count} students.</p>"

    return body



def showAllRooms(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT number, capacity FROM room")

    ## create an HTML table for output:
    body = """
    <a href="/">Back to Course List</a>
    <h2>Room List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1"><b>Room</b></font></td>
        <td><font size=+1"><b>Capacity</b></font></td>
        <td><font size=+1"><b>delete</b></font></td>
      </tr>
    """

    count = 0
    # each iteration of this loop creates on row of output:
    for room_number, room_capacity in cursor:
        body += (
            "<tr>"
            f"<td><a href='?action=get_room&room_number={room_number}'>{escape(room_number)}</a></td>"
            f"<td>{room_capacity}</td>"
            "<td><form method='post' action='/'>"
            f"<input type='hidden' NAME='room_number' VALUE='{room_number}'>"
            f"<input type='hidden' NAME='action' VALUE='delete_room'>"
            '<input type="submit" name="deleteRoom" value="Delete">'
            "</form></td>"
            "</tr>\n"
        )
        count += 1

    body += "</table>" f"<p>Found {count} rooms.</p>"

    return body

def showAllCourses(conn):
    cursor = conn.cursor()

    sql = """
    SELECT course.number, title, room, count(enrolled.student) AS enrolled, capacity
    FROM course JOIN room ON room.number = course.room
    LEFT JOIN enrolled ON enrolled.course = course.number
    GROUP BY course.number, title, room, capacity
    """

    cursor.execute(sql)

    ## create an HTML table for output:
    body = """
    <h2>Course List</h2>
    <p>
    <table border=1>
      <tr>
        <td><font size=+1"><b>Course</b></font></td>
        <td><font size=+1"><b><a href="/?action=list_rooms">Room</a></b></font></td>
        <td><font size=+1"><b><a href="/?action=list_students">Enrolled</a></b></font></td>
        <td><font size=+1"><b>Capacity</b></font></td>
        <td><font size=+1"><b>delete</b></font></td>
      </tr>
    """

    count = 0
    # each iteration of this loop creates on row of output:
    for course_number, course_name, room_number, email, activities in cursor:
        body += (
            "<tr>"
            f"<td><a href='?action=get_course&course_number={course_number}'>{course_name}</a></td>"
            f"<td><a href='?action=get_room&room_number={room_number}'>{room_number}</a></td>"
            f"<td>{email}</td>"
            f"<td>{activities}</td>"
            "<td><form method='post' action='/'>"
            f"<input type='hidden' NAME='course_number' VALUE='{course_number}'>"
            f"<input type='hidden' NAME='action' VALUE='delete_course'>"
            '<input type="submit" name="deleteCourse" value="Delete">'
            "</form></td>"
            "</tr>\n"
        )
        count += 1

    body += "</table>" f"<p>Found {count} courses.</p>"

    return body

def showAddStudentForm():
    return f"""
    <h2>Add A Student</h2>
    <p>
    <FORM METHOD="POST">
    <table>
        <tr>
            <td>Student ID</td>
            <td><INPUT TYPE="TEXT" NAME="student_id" pattern="[0-9]+"></td>
        </tr>
        <tr>
            <td>Student Name</td>
            <td><INPUT NAME="student_name" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input hidden name="action" value="add_student">
            <input type="submit" value="Add!">
            </td>
        </tr>
    </table>
    </FORM>
    """


def showAddRoomForm():
    return f"""
    <h2>Add A Room</h2>
    <p>
    <FORM METHOD="POST">
    <table>
        <tr>
            <td>Room Name</td>
            <td><INPUT TYPE="TEXT" NAME="room_number" placeholder="BUILDING 123"></td>
        </tr>
        <tr>
            <td>Room Capacity</td>
            <td><INPUT TYPE="number" NAME="room_capacity" VALUE=""></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input hidden name="action" value="add_room">
            <input type="submit" value="Add!">
            </td>
        </tr>
    </table>
    </FORM>
    """


def showAddCoursesForm(conn):

    cursor = conn.cursor()
    sql = """
    SELECT number
    FROM room
    """
    cursor.execute(sql)

    return f"""
    <h2>Add A Course</h2>
    <p>
    <FORM METHOD="POST">
    <table>
        <tr>
            <td>Course Name</td>
            <td><INPUT TYPE="TEXT" NAME="course_name" VALUE=""></td>
        </tr>
        <tr>
            <td>Course Number</td>
            <td><INPUT TYPE="TEXT" NAME="course_number" VALUE="" placeholder="DEPT 100"></td>
        </tr>
        <tr>
            <td>Room</td>
            <td><SELECT NAME="course_room">
            
            { "".join( f"<option>{room}</option>" for room, in cursor ) }
            
            </SELECT></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input hidden name="action" value="add_course">
            <input type="submit" value="Add!">
            </td>
        </tr>
    </table>
    </FORM>
    """

def getStudent(conn, student_id):
    # First, get current data for this room
    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM student
    WHERE id=%s
    """
    cursor.execute(sql, (student_id,))

    data = cursor.fetchall()

    # Create a form to update this course
    student_id, student_name = data[0]

    return """
    <a href="javascript:history.back()">Back</a>
    <h2>View and Edit Student #%s</h2>
    <p>
    <FORM METHOD="POST" action="/">
    <table>
        <tr>
            <td>Student Name</td>
            <td><input name="student_name" value="%s"></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input type="hidden" name="student_id" value="%s">
            <input hidden name="action" value="update_student">
            <input type="submit" value="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """ % (
        student_id,
        student_name,
        student_id
    )


def getRoom(conn, room_number):
    # First, get current data for this room
    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM room
    WHERE number=%s
    """
    cursor.execute(sql, (room_number,))

    data = cursor.fetchall()

    # Create a form to update this course
    room_number, room_capacity = data[0]

    return """
    <a href="javascript:history.back()">Back</a>
    <h2>View and Edit Room %s</h2>
    <p>
    <FORM METHOD="POST" action="/">
    <table>
        <tr>
            <td>Room Capacity</td>
            <td><input name="room_capacity" type="number" value="%s"></td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input type="hidden" name="room_number" value="%s">
            <input hidden name="action" value="update_room">
            <input type="submit" value="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """ % (
        room_number,
        room_capacity,
        room_number
    )


def getCourse(conn, course_number):
    # First, get current data for this profile
    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM course
    WHERE number=%s
    """
    cursor.execute(sql, (course_number,))

    data = cursor.fetchall()

    # Create a form to update this course
    course_number, course_name, course_room = data[0]

    # get rooms to fill dropdown
    cursor.execute("SELECT number FROM room")

    return """
    <a href="javascript:history.back()">Back</a>
    <h2>View and Edit Course %s</h2>
    <p>
    <FORM METHOD="POST">
    <table>
        <tr>
            <td>Course Name</td>
            <td><INPUT TYPE="TEXT" NAME="course_name" VALUE="%s" size="50"></td>
        </tr>
        <tr>
            <td>Course Room</td>
            <td><SELECT NAME="course_room">
            %s
            </SELECT>
            </td>
        </tr>
        <tr>
            <td></td>
            <td>
            <input type="hidden" name="course_number" value="%s">
            <input hidden name="action" value="update_course">
            <input type="submit" value="Update!">
            </td>
        </tr>
    </table>
    </FORM>
    """ % (
        course_number,
        course_name,
        "".join( f"<option { 'selected' if room == course_room else '' }>{room}</option>" for room, in cursor ),
        course_number
    )

def check_student_info(student_id, student_name, action_verb):
    try:
        student_id = int(student_id)
        if student_id <= 0:
            return f"Couldn't {action_verb} student: ID cannot be negative"
    except ValueError:
        return f"Couldn't {action_verb} student: make sure student ID is a number"
    if student_name == "":
        return f"Couldn't {action_verb} student: make sure name isn't blank"


def check_room_info(room_number, room_capacity, action_verb):
    try:
        room_capacity = int(room_capacity)
        if room_capacity <= 0:
            return f"Couldn't {action_verb} room: capacity must be more than 0"
    except ValueError:
        return f"Couldn't {action_verb} room: make sure room capacity is a positive number"
    if not VALID_ROOM_NUMBER_REGEX.match(room_number):
        return f"Couldn't {action_verb} room: make sure number follows format ABCD 1234 (BUILDING, then number)"


def check_course_info(course_name, course_number, course_room, action_verb):
    if course_name == "":
        return f"Couldn't {action_verb} course: make sure name is non-blank"
    if not VALID_COURSE_NUMBER_REGEX.match(course_number):
        return f"Couldn't {action_verb} course: make sure number follows format ABCD 1234 (DEPT, then number)"


def delayed_redirect(address, seconds = 5, label=None):

    if type(label) == str:
        label = "to " + label
    elif label == None:
        label = "back"
    else:
        label = str(label)

    seconds_explanation = f"in {seconds} seconds" if seconds > 0 else "shortly"

    return """
    <p>Redirecting <a href="%s">%s</a>...<span class="redir-seconds">If you are not redirected %s, please click the link.</span></p>
    <script>
        setTimeout(function() {
            window.location.replace("%s");
        }, %s)
    </script>
    """ % ( escape(address), label, seconds_explanation, address, seconds * 1000 )

def updateStudent(conn, student_id, student_name):
    err = check_student_info(student_id, student_name, "update")
    if err:
        return err
    
    cursor = conn.cursor()

    sql = "UPDATE student SET name=%s WHERE id=%s"
    params = (student_name, student_id)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Update Student Succeeded. " + delayed_redirect(f"/?action=list_students",0)
    else:
        return "Update Student Failed. Please try again." + delayed_redirect(f"/?action=list_students")



def updateRoom(conn, room_number, room_capacity):
    err = check_room_info(room_number, room_capacity, "update")
    if err:
        return err
    
    cursor = conn.cursor()

    sql = "UPDATE room SET capacity=%s WHERE number=%s"
    params = (room_capacity, room_number)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Update Room Succeeded. " + delayed_redirect(f"/?action=list_rooms",0)
    else:
        return "Update Room Failed. Please try again." + delayed_redirect(f"/?action=list_rooms")


def updateCourse(conn, course_name, course_number, course_room):
    err = check_course_info(course_name, course_number, course_room, "update")
    if err:
        return err
    
    cursor = conn.cursor()

    sql = "UPDATE course SET title=%s, room=%s WHERE number=%s"
    params = (course_name, course_room, course_number)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Update Course Succeeded. " + delayed_redirect(f"/", 0)
    else:
        return "Update Course Failed. Please try again." + delayed_redirect(f"/")

def addRoom(conn, room_number, room_capacity):
    cursor = conn.cursor()

    err = check_room_info(room_number, room_capacity, "create")
    if err:
        return err+ delayed_redirect("/?action=list_rooms")

    sql = "INSERT INTO room VALUES (%s,%s)"
    params = (room_number, room_capacity)

    try: 
        cursor.execute(sql, params)
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        return f"Add Room Failed: room {escape(room_number)} already exists."+ delayed_redirect("/?action=list_rooms")
    
    if cursor.rowcount > 0:
        return "Add Room Succeeded." + delayed_redirect("/?action=list_rooms")
    else:
        return "Add Room Failed."+ delayed_redirect("/?action=list_rooms")

def addStudent(conn, student_id, student_name):
    cursor = conn.cursor()

    err = check_student_info(student_id, student_name, "create")
    if err:
        return err+ delayed_redirect("/?action=list_students")

    sql = "INSERT INTO student VALUES (%s,%s)"
    params = (student_id, student_name)

    try: 
        cursor.execute(sql, params)
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        return f"Add Student Failed: student with ID {student_id} already exists."+ delayed_redirect("/?action=list_students")
    
    if cursor.rowcount > 0:
        return "Add Student Succeeded." + delayed_redirect("/?action=list_students", 0)
    else:
        return "Add Student Failed."+ delayed_redirect("/?action=list_students")



def addCourse(conn, course_name, course_number, course_room):
    cursor = conn.cursor()

    err = check_course_info(course_name, course_number, course_room, "create")
    if err:
        return err

    sql = "INSERT INTO course VALUES (%s,%s,%s)"
    params = (course_name, course_number, course_room)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Add Course Succeeded." + delayed_redirect("/")
    else:
        return "Add Course Failed." + delayed_redirect("/")

def deleteRoom(conn, room_number):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM room WHERE number = %s", (room_number,))
        conn.commit()
    except psycopg2.errors.ForeignKeyViolation:
        return "Delete Room Failed: Please make sure no courses are using this room before deleting it." + delayed_redirect("/?action=list_rooms")
    
    if cursor.rowcount > 0:
        return "Delete Room Succeeded." + delayed_redirect("/?action=list_rooms", 0)
    else:
        return "Delete Room Failed." + delayed_redirect("/?action=list_rooms")


def deleteStudent(conn, student_id):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM student WHERE id = %s", (student_id,))
        conn.commit()
    except psycopg2.errors.ForeignKeyViolation:
        return "Delete Student Failed: Please make sure this student is not enrolled in any courses before deleting them." + delayed_redirect("/?action=list_students")
    
    if cursor.rowcount > 0:
        return "Delete Student Succeeded." + delayed_redirect("/?action=list_students", 0)
    else:
        return "Delete Student Failed." + delayed_redirect("/?action=list_students")


def deleteCourse(conn, course_number):
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM course WHERE number = %s", (course_number,))
        conn.commit()
    except psycopg2.errors.ForeignKeyViolation:
        return "Delete Course Failed: Please make sure to unenroll all students before deleting course." + delayed_redirect("/")
    
    if cursor.rowcount > 0:
        return "Delete Course Succeeded." + delayed_redirect("/")
    else:
        return "Delete Course Failed." + delayed_redirect("/")


def get_qs_post(env):
    """
    :param env: WSGI environment
    :returns: A tuple (qs, post), containing the query string and post data,
              respectively
    """
    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(env.get("CONTENT_LENGTH", 0))
    except (ValueError):
        request_body_size = 0
    # When the method is POST the variable will be sent
    # in the HTTP request body which is passed by the WSGI server
    # in the file like wsgi.input environment variable.
    request_body = env["wsgi.input"].read(request_body_size).decode("utf-8")
    post = parse_qs(request_body)
    return parse_qs(env["QUERY_STRING"]), post

def get_body_content(get_param, conn):
    action = get_param("action")
    # Default action: list courses
    if not action:
        action = "list_courses"

    if action == "add_course":
        return addCourse(
            conn,
            get_param("course_name"),
            get_param("course_number"),
            get_param("course_room")
        )
    elif action == "list_courses":
        return showAllCourses(conn) + showAddCoursesForm(conn)
    elif action == "get_course":
        return getCourse(
            conn,
            get_param("course_number")
        )
    elif action == "update_course":
        return updateCourse(conn, 
            get_param("course_name"),
            get_param("course_number"),
            get_param("course_room")
        )
    elif action == "delete_course":
        return deleteCourse(conn, get_param("course_number"))
    elif action == "add_room":
        return addRoom(conn, 
            get_param("room_number"), 
            get_param("room_capacity")
        )
    elif action == "list_rooms":
        return showAllRooms(conn) + showAddRoomForm()
    elif action == "get_room":
        return getRoom(
            conn,
            get_param("room_number")
        )
    elif action == "update_room":
        return updateRoom(conn, 
            get_param("room_number"),
            get_param("room_capacity")
        )
    elif action == "delete_room":
        return deleteRoom(conn, get_param("room_number"))
    elif action == "add_student":
        return addStudent(conn, 
            get_param("student_id"),
            get_param("student_name")
        )
    elif action == "list_students":
        return showAllStudents(conn) + showAddStudentForm()
    elif action == "get_student":
        return getStudent(
            conn,
            get_param("student_id")
        )
    elif action == "update_student":
        return updateStudent(conn, 
            get_param("student_id"),
            get_param("student_name")
        )
    elif action == "delete_student":
        return deleteStudent(conn, get_param("student_id"))
    # If an action was specified which is invalid
    else:
        return "Error 404: page not found or could not be rendered."

def application(env, start_response):
    qs, post = get_qs_post(env)

    # No semantic difference on the backend of
    # this app between query params and post data.
    # While there is a semantic difference on the FRONT
    # end (mainly relating to maximum length of the GET url
    # and visibility to the user), the backend doesn't care.
    # Everything is "secure" already once it's gotten to the backend,
    # since this site has no access control. Therefore, this backend
    # combines the two sets of parameters early on to eliminate any
    # source of confusion (e.g. "is paramater `x` in `qs` or `post`?")
    qs.update(post)
    params = qs

    body = ""
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )
    except psycopg2.Warning as e:
        print(f"Database warning: {e}")
        body += "Check logs for DB warning"
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        body += "Check logs for DB error"

    body += get_body_content(lambda p: params.get(p, [""])[0], conn)

    start_response("200 OK", [("Content-Type", "text/html")])
    return [wrapBody(body, title="Mini Facebook").encode("utf-8")]