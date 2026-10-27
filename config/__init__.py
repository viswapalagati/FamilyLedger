"""Register PyMySQL as the ``MySQLdb`` driver so no C build toolchain is needed."""

import pymysql

pymysql.install_as_MySQLdb()
