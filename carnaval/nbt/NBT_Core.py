# ============================================================================ #
#                                  NBT_Core.py
#
# Copyright:
#   Copyright (C) 2014 by Christopher R. Hertel
#
# $Id: NBT_Core.py; 2016-08-14 14:06:39 -0500; Christopher R. Hertel$
#
# ---------------------------------------------------------------------------- #
#
# Description:
#   NetBIOS over TCP/IP (IETF STD19) implementation: Core components.
#
# ---------------------------------------------------------------------------- #
#
# License:
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 3.0 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this library.  If not, see <http://www.gnu.org/licenses/>.
#
# See Also:
#   The 0.README file included with the distribution.
#
# ---------------------------------------------------------------------------- #
#              This code was developed in participation with the
#                   Protocol Freedom Information Foundation.
#                          <www.protocolfreedom.org>
# ---------------------------------------------------------------------------- #
#
# Notes:
#
#   The NBT transport protocol is a virtual LAN protocol.  It is used to
#   emulate the behavior of the old IBM PC Network and NetBIOS Frame (NBF)
#   protocol networks.  Note that NetBIOS and NetBEUI are APIs, not network
#   protocols.  NBT provides a mechanism by which the NetBIOS and NetBEUI
#   APIs can be mapped to TCP/UDP.  For more detailed information, see the
#   references given in the docstring below.
#
#   On a DOS, OS/2, or Windows platform, various transport layers are
#   available that support the NetBIOS/NetBEUI API.  Of these, NBT has
#   emerged as the most popular and most commonly used.
#
#   - The modules in the NBT suite are written to run under Python v2.7.
#     Some attempts have been made to provide compatibility with older
#     versions, but little or no testing has been done.  Patches are
#     welcome, but see the 0.Readme.txt file for notes on submissions.
#     No attempt at all has been made at Python 3 compatability.
#
#   - This module makes use of class methods, which seem to confuse a
#     lot of people (including yours truly).  This write-up was quite
#     useful:
# http://julien.danjou.info/blog/2013/guide-python-static-class-abstract-methods
#
# ============================================================================ #
#
"""NetBIOS over TCP/UDP (NBT) protocol: Core Components

Classes, functions, and other objects used throughout this NBT Transport
implementation.  Fundamental stuff.

The NBT transport protocol is made of of three services:
  NBT Name Service     - Maps NetBIOS endpoint names to IPv4 addresses.
  NBT Datagram Service - NetBIOS datagram distribution over UDP.
  NBT Session Service  - NetBIOS sessions over TCP.

NBT is defined in IETF RFCs 1001 and 1002, collectively known as IETF
Standard 19 (STD19).  A detailed implementer's guide to NBT can be
found on the web at:
  http://www.ubiqx.org/cifs/NetBIOS.html

References:
  Implementing CIFS: The Common Internet File System
    http://www.ubiqx.orc/cifs/
  RFC 1001: PROTOCOL STANDARD FOR A NetBIOS SERVICE ON A TCP/UDP
            TRANSPORT: CONCEPTS AND METHODS
    http://www.rfc-editor.org/rfc/rfc1001.txt
  RFC 1002: PROTOCOL STANDARD FOR A NetBIOS SERVICE ON A TCP/UDP
            TRANSPORT: DETAILED SPECIFICATIONS
    http://www.rfc-editor.org/rfc/rfc1002.txt
  [MS-NBTE]: NetBIOS over TCP (NBT) Extensions
    http://msdn.microsoft.com/en-us/library/dd891412.aspx
"""

# Imports -------------------------------------------------------------------- #
#
#   ErrorCodeExceptions - Provides the CodedError() class, upon which the
#                         NBTerror class is built.
#

from common.ErrorCodeExceptions import CodedError


# Classes -------------------------------------------------------------------- #
#

class NBTerror( CodedError ):
  """NBT errors.

  A set of error codes, defined by numbers (starting with 1000)
  specific to the NBT transport implementation.

  Class Attributes:
    error_dict  - A dictionary that maps error codes to descriptive
                  names.  This dictionary defines the set of valid
                  NBTerror error codes.

  Error Codes:
    1000  - Warning.
    1001  - NBT Syntax Error encountered.
    1002  - NBT Semantic Error encountered.
    1003  - RFC883 Label String Pointer (LSP) encountered.
    1004  - An LSP was expected, but not found.
    1005  - NBT message could not be parsed.

  See Also: common.ErrorCodeExceptions.CodedError

  Code 1000 represents a warning.  Warnings may be safely caught and
  ignored, or reported, or otherwise handled.  Warnings should only be
  raised when it is safe to continue without taking any particular
  action.

  Doctest:
    >>> print NBTerror.errStr( 1002 )
    NBT Semantic Error
    >>> a, b = NBTerror.errRange()
    >>> (a < b) and (1000 == a)
    True
    >>> NBTerror()
    Traceback (most recent call last):
      ...
    ValueError: Undefined error code: None.
    >>> s = 'Mein Luftkissenfahrzeug ist voller Aale'
    >>> print NBTerror( 1005, s )
    1005: Malformed Message; Mein Luftkissenfahrzeug ist voller Aale.
  """
  error_dict = {
    1000 : "Warning",
    1001 : "NBT Syntax Error",
    1002 : "NBT Semantic Error",
    1003 : "Label String Pointer",
    1004 : "No Label String Pointer",
    1005 : "Malformed Message"
    }


class dLinkedList( object ):
  """
  Doubly-linked list.

  A simple implementation of a doubly-linked list.

  This implementation is intentionally simple.  It is missing a few
  conveniences, such as a count of the nodes in the list, and it does
  no error checking.  Be careful.

  Instance Attributes:
    Head  - The first node in the list.
    Tail  - The last node in the list.

  If the list is empty, both <Head> and <Tail> will be None.

  Doctest:
    >>> lst = dLinkedList()
    >>> [ d for d in lst.elements() ]
    []
    >>> for i in range( 1, 6 ):
    ...   lst.insert( dLinkedList.Node( "node0"+str(i) ) )
    >>> lst.remove( lst.Head )
    >>> lst.remove( lst.Tail )
    >>> n = lst.Head.Next.Next
    >>> n.Data
    'node02'
    >>> lst.remove( n )
    >>> [ d for d in lst.elements() ]
    ['node04', 'node03']
  """

  class Node( object ):
    """A node in the doubly-linked list.

    Instance Attributes:
      Next  - The next node in the linked list, or None to indicate the
              end of the list.
      Prev  - The previous node in the linked list, or None to indicate
              that the current node is the first node in the list.
      Data  - The payload of the node.  That is, whatever it is that
              the user is storing within the node.

    Note: The attribute names all begin with an upper case letter
          because "next" is the name of a Python built-in function (see
          https://docs.python.org/2/library/functions.html#next).
    """
    def __init__( self, Data=None ):
      """Create and initialize a <dLinkedList> node.

      Input:
        Data  - Node payload; the data being stored within the linked
                list node.
      """
      self.Next = self.Prev = None
      self.Data = Data

  def __init__( self ):
    """Create and initialize a <dLinkedList> list.
    """
    self.Head = None
    self.Tail = None

  def insert( self, newNode=None, after=None ):
    """Add a <dLinkedList.Node()> object to an existing list.

    Input:
      newNode - The new <dLinkedList.Node()> object to be inserted.
      after   - An optional node, that is already included in the list,
                after which the new node is to be inserted.  If this is
                None, the new node will be inserted at the head of the
                list.
    """
    if( after ):
      newNode.Next = after.Next
      after.Next   = newNode
    else:
      newNode.Next = self.Head
      self.Head    = newNode
    newNode.Prev = after
    if( newNode.Next ):
      newNode.Next.Prev = newNode
    else:
      self.Tail = newNode

  def remove( self, oldNode ):
    """Remove a node from the list.

    Input:
      oldNode - The node to be removed from the list.
    """
    if( oldNode.Prev is None ):
      self.Head = oldNode.Next
    else:
      oldNode.Prev.Next = oldNode.Next

    if( oldNode.Next is None ):
      self.Tail = oldNode.Prev
    else:
      oldNode.Next.Prev = oldNode.Prev

  def elements( self ):
    """A generator that iterates the Data fields from within the list.
    """
    n = self.Head
    while( n is not None ):
      yield n.Data
      n = n.Next

# ============================================================================ #
# "Fussbudgetry!", exclaimed Sally.  Then, after hesitating just long enough
# to make it seem awkward, she stomped her foot.  Jennifer, in a clear act of
# contempt, responded by spilling Sally's milk, which ran across the table
# and dribbled upon the floor, much to the delight of the kittens.
# ============================================================================ #
