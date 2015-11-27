.. _admin:

The Admin Area
==============

Indigo has a backend Admin area that lets adminstrator users control some internal settings of how Indigo works. Only adminstrator (staff) users have access to this area.

Logging In
----------

To log into the Admin area:

1. Log into Indigo 
2. Click your name in the top-right corner
3. Click **Site Settings**

.. note:: If the **Site Settings** option isn't visible, then you aren't a staff member and don't have permission to view the admin area.

Permissions
-----------

Indigo uses Django's permission system to control who can create, edit, delete and publish documents. This can help prevent documents from being deleted
and published accidentally.

Permissions can be assigned to individual users, or to **groups**. Users who belong to groups get permissions from those groups.

To edit permissions,

1. Click on **Users** or **Groups** in the Admin area.
2. Choose the user or group to edit (or create a new user or group)
3. Scroll down to the permissions boxes.

The permissions that are important are:

**indigo_api | document | Can add document**
		Allows the user to create and import a new document. This doesn't allow a user to edit existing documents.

**indigo_api | document | Can change document**
		Allows the user to edit existing documents.

**indigo_api | document | Can delete document**
		Allows the user to delete documents.

**indigo_api | document | Can publish and edit non-draft documents**
		Allows the user to mark a document as *published (not a draft)* and, along with the *change* permission, edit published documents.

.. note:: Only give the **delete** and **publish** permissions to experienced users.

Adding New Admins
-----------------

To give admin permissions to a user, which allows them to log into the Admin area:

1. Click on **Users** in the Admin area.
2. Click on the user you wish to make an Admin.
3. Check the **Staff status** checkbox in the Permissions section and click Save.
