# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: status.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='status.proto',
  package='',
  syntax='proto2',
  serialized_pb=_b('\n\x0cstatus.proto\"C\n\x06Status\x12\x1a\n\x04type\x18\x01 \x01(\x0e\x32\x0c.Status.Type\"\x1d\n\x04Type\x12\x08\n\x04\x46\x41IL\x10\x00\x12\x0b\n\x07SUCCESS\x10\x01')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_STATUS_TYPE = _descriptor.EnumDescriptor(
  name='Type',
  full_name='Status.Type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='FAIL', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='SUCCESS', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=54,
  serialized_end=83,
)
_sym_db.RegisterEnumDescriptor(_STATUS_TYPE)


_STATUS = _descriptor.Descriptor(
  name='Status',
  full_name='Status',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='Status.type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _STATUS_TYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=16,
  serialized_end=83,
)

_STATUS.fields_by_name['type'].enum_type = _STATUS_TYPE
_STATUS_TYPE.containing_type = _STATUS
DESCRIPTOR.message_types_by_name['Status'] = _STATUS

Status = _reflection.GeneratedProtocolMessageType('Status', (_message.Message,), dict(
  DESCRIPTOR = _STATUS,
  __module__ = 'status_pb2'
  # @@protoc_insertion_point(class_scope:Status)
  ))
_sym_db.RegisterMessage(Status)


# @@protoc_insertion_point(module_scope)
