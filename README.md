### cloudshell_admin_toolbox_service 

---
**Admin Only Service Shell for Quali's CloudShell**

- www.tsieda.com
- www.quali.com/cloudshell-pro

This is a 2nd Gen Service Shell for use with in a Sandbox (CloudShell Reservation).
It provides a series of of commands that are either not directly available, 
or require the use of other tools that are outside of the Sandbox.

**Commands are broken into 2 sections:**
1. Resource Commands
2. Reservation Commands

---
**Resource Commands**

Resource Commands all have a 'target' input.  
This will be the name of the resource you wish to query.
All resources need to be with in the current sandbox to be valid for query.
Child resources are also valid, as long as they are with in the sandbox.
In addition, you'll need to specify the full name for the child resource:  'TestCenter_12/Card_5/Port_2'

Commands:
* Set Resource Live Status
    * Changes the Resource's Live Status (Icon) visible on the Canvas
    * Pull down to select available options (matching default configuration)
* Get Summary
    * Prints to the Output window a basic summary of the resource
* Get Reservations
    * Returns all reservations associated for the resource for the next 30 days
* Get Attributes
    * Returns a list of all Attributes and their current values for the Resource
        * Some attributes are not normally visible from the canvas
    * Option to decrypt password type attributes (Why this is an Admin only Service)
        * Designed to allow for validation of configuration
    * Returns the list as a short-hand, meaning if it is a Gen2 Shell the prefix to the attribute name is removed
* Set Attribute Value
    * Sets the attribute to a new value.
        * not all attributes can be altered via this method (often linked to the discovery process)
    * Attribute names can be entered without Gen2 Prefixes, allowing the return from Get Attributes to be used
* Get Children
    * Returns a list of all Child Resources, including ones not in the current sandbox
* Get Connections
    * Returns a list of all connections mapped to this resource, including on children not currently in the sandbox.
        * Helpful if an additional route needs to be figured out
        
---
**Reservation Commands**

Reservation Commands either manipulate the Reservation, or queries for all items in the Reservation (Sandbox)

Commands:
* List Reservation Assets
    * Returns a list of all assets associated with the Sandbox, by Type, with any children grouped under
* Get Current Reservation Info
    * Returns a summary of the Sandbox/Reservation details
* Set Reservation Live Status
    * Allows the Sandbox's (Reservation's) Live Status to be changed
    * Pull down option is matched to Quali Defaults
* Get All Reservations
    * Returns a list of all current and upcoming reservations for all resources in the Sandbox
* Get Sandbox Data
    * Returns the information in the 'Sandbox Data'
    * This is an internal record to the sandbox
    * Simple flat Key:Value storage
        * Value can be more complex data structure
* Set Sandbox Data by Key
    * Creates/Updates the Value of a Key in the Sandbox Data
* Clear Sandbox Data
    * Sets the Sandbox Data to a Null/Blank value
     


