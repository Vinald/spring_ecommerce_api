import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class App(Base):
    __tablename__ = 'apps'

    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    phone = Column(String(40), nullable=True)
    toll_free = Column(String(40), nullable=True)
    caller_id = Column(String(40), nullable=True)
    voice_url = Column(String(500), nullable=True)
    status_url = Column(String(500), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_modified = Column(DateTime, nullable=True)


class CDR(Base):
    __tablename__ = 'cdr'

    id = Column(Integer, primary_key=True)
    app_name = Column(String(40), nullable=False)
    creation_date = Column(DateTime, default=datetime.datetime.now)
    call_start_time = Column(String(10), nullable=True)
    call_end_time = Column(String(10), nullable=True)
    duration = Column(Integer, nullable=True, default=0)
    caller_id = Column(String(20), nullable=False)
    dialed_number = Column(String(20), nullable=False)
    call_state = Column(String(40), nullable=True)
    peer = Column(String(40), nullable=True)
    call_direction = Column(String(30), nullable=False)
    token = Column(String(255), nullable=True)
    call_id = Column(String(255), nullable=True)
    external_id = Column(String(255), nullable=True)


class ReportType(Base):
    __tablename__ = 'report_types'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    sql = Column(Text(), nullable=False)
    creation_date = Column(DateTime, default=datetime.datetime.now, nullable=False)
    modification_date = Column(DateTime, nullable=True)


class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type_id = Column(Integer, ForeignKey('report_types.id'), nullable=False)
    report_type = relationship("ReportType")
    scheduled = Column(Integer, nullable=False)
    cron_expression = Column(String(100), nullable=True)
    recipients_to = Column(Text, nullable=True)
    recipients_cc = Column(Text, nullable=True)
    creation_date = Column(DateTime, default=datetime.datetime.now, nullable=False)
    modification_date = Column(DateTime, nullable=True)
    time = Column(String(8), nullable=True)
    day = Column(String(2), nullable=True)
    recurrence = Column(String(20), nullable=True)
