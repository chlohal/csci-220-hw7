import re
import os
import time
from urllib.parse import parse_qs
from html import escape

import psycopg2

VALID_COURSE_NUMBER_REGEX = re.compile(r"^\w{2,} \d{2,}$")

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
        <td><font size=+1"><b>Room</b></font></td>
        <td><font size=+1"><b>Enrolled</b></font></td>
        <td><font size=+1"><b>Capacity</b></font></td>
        <td><font size=+1"><b>delete</b></font></td>
      </tr>
    """

    count = 0
    # each iteration of this loop creates on row of output:
    for course_number, course_name, room_number, email, activities in cursor:
        body += (
            "<tr>"
            f"<td><a href='?course_number={course_number}'>{course_name}</a></td>"
            f"<td><a href='?room_number={room_number}'>{room_number}</a></td>"
            f"<td>{email}</td>"
            f"<td>{activities}</td>"
            "<td><form method='post' action='miniFacebook.py'>"
            f"<input type='hidden' NAME='course_number' VALUE='{course_number}'>"
            '<input type="submit" name="deleteCourse" value="Delete">'
            "</form></td>"
            "</tr>\n"
        )
        count += 1

    body += "</table>" f"<p>Found {count} courses.</p>"

    return body


def showProfilePage(conn, idNum):
    body = """
    <a href="./miniFacebook.py">Return to main page.</a>
    """

    cursor = conn.cursor()

    sql = """
    SELECT *
    FROM profiles
    WHERE id=%s
    """
    cursor.execute(sql, (int(idNum),))

    data = cursor.fetchall()

    # show profile information
    (idNum, lastname, firstName, email, activities) = data[0]

    body += """
    <h2>%s %s's Profile Page</h2>
    <p>
    <table border=1>
        <tr>
            <td>Email</td>
            <td>%s</td>
        </tr>
        <tr>
            <td>Activities</td>
            <td>%s</td>
        </tr>
    </table>
    """ % (
        firstName,
        lastname,
        email,
        activities,
    )

    # provide an update button:
    body += (
        """
    <FORM METHOD="POST" action="miniFacebook.py">
    <INPUT TYPE="HIDDEN" NAME="idNum" VALUE="%s">
    <INPUT TYPE="SUBMIT" NAME="showUpdateProfileForm" VALUE="Update Profile">
    </FORM>
    """
        % idNum
    )

    # Get and display all status message for this person
    sql = """
    SELECT DateTime, Message
    FROM status
    WHERE profile_id=%s
    """

    cursor.execute(sql, (int(idNum),))

    data = cursor.fetchall()

    body += """
    <h2>Status Updates</h2>
    <p>
    <table border=1>
        <tr>
          <td>DateTime</td>
          <td>Message</td>
        </tr>
    """

    for row in data:

        body += (
            """
        <tr>
          <td>%s</td>
          <td>%s</td>
        </tr>
        """
            % row
        )

    body += """
    </table>
    """

    # Add form to let user update their status message
    body += (
        """
    <FORM METHOD="POST" action="miniFacebook.py">
    <INPUT TYPE="HIDDEN" NAME="idNum" VALUE="%s">
	<input type="text" name="message" value="Enter a new status...">
    <INPUT TYPE="SUBMIT" NAME="processStatusUpdate" VALUE="Update Status">
    </FORM>
    """
        % idNum
    )
    return body


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
            <input type="submit" name="add_course" value="Add!">
            </td>
        </tr>
    </table>
    </FORM>
    """


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
            <input type="hidden" name="idNum" value="%s">
            <input type="submit" name="update_course" value="Update!">
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

def check_course_info(course_name, course_number, course_room, action_verb):
    if course_name == "":
        return f"Couldn't {action_verb} course: make sure name is non-blank"
    if not VALID_COURSE_NUMBER_REGEX.match(course_number):
        return f"Couldn't {action_verb} course: make sure number follows format ABCD 1234 (DEPT, then number)"

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
        return "Update Course Succeeded."
    else:
        return "Update Course Failed."

def addCourse(conn, course_name, course_number, course_room):
    cursor = conn.cursor()

    err = check_course_info(course_name, course_number, course_room, "update")
    if err:
        return err

    sql = "INSERT INTO course VALUES (%s,%s,%s)"
    params = (course_name, course_number, course_room)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Add Course Succeeded."
    else:
        return "Add Course Failed."


def updateStatusMessage(conn, idNum, message):
    cursor = conn.cursor()

    tm = time.localtime()
    nowtime = "%04d-%02d-%02d %02d:%02d:%02d" % tm[0:6]

    sql = "INSERT INTO status(profile_id, message, dateTime) VALUES (%s,%s,%s)"
    params = (idNum, message, nowtime)
    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Succeeded."
    else:
        return "Failed."


def processProfileUpdate(conn, idNum, lastname, firstname, email, activities):
    cursor = conn.cursor()

    sql = "UPDATE profiles SET lastname=%s, firstname=%s, email=%s, activities=%s WHERE id = %s"
    params = (lastname, firstname, email, activities, idNum)

    cursor.execute(sql, params)
    conn.commit()

    if cursor.rowcount > 0:
        return "Update Profile Succeeded."
    else:
        return "Update Profile Failed."


def deleteCourse(conn, course_number):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM course WHERE number = %s", (course_number,))
    conn.commit()
    if cursor.rowcount > 0:
        return "Delete Course Succeeded."
    else:
        return "Delete Course Failed."


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


def application(env, start_response):
    qs, post = get_qs_post(env)

    # No semantic difference on the backend of
    # this app between query params and post data --
    # combine them
    qs.update(post)
    params = qs

    def param(p):
        return params.get(p, [""])[0]

    body = ""
    try:
        conn = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
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

    if "add_course" in params:
        body += addCourse(
            conn,
            param("course_name"),
            param("course_number"),
            param("course_room")
        )
    elif "update_course" in params:
        body += updateCourse(conn, 
            param("course_name"),
            param("course_number"),
            param("course_room")
        )
    elif "course_number" in params:
        body += getCourse(
            conn,
            param("course_number")
        )
    # default case: show all courses
    else:
        body += showAllCourses(conn)
        body += showAddCoursesForm(conn)

    start_response("200 OK", [("Content-Type", "text/html")])
    return [wrapBody(body, title="Mini Facebook").encode("utf-8")]