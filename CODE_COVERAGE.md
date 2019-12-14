**The following files/functions/classes have nnot been tested thereby reducing Code Coverage**
**ANALYTICS APP:**
	- URLs are not tested at all (urls.py)
	- The serializers are not tested at all (serializers.py)

**BASE APP:**
	- The utilities (utils.py) are not tested eg. send_email, get_url_from_hostname, etc.
	- There are no tests for models (models.py)

**ACCOUNTS APP:**
	- Serializers are not tested (serializers.py)

**CHALLENGES APP:**
	**- In the models.py file:**
		- Challenge Configuration is not tested.
		- Star Challenge is not tested.
		- User limitation is not tested.

	- Amazon Web Services utils are not tested at all (aws-utils.py)

**HOSTS APP:**
	- Searializers (serializers.py) are not tested

**JOBS APP:**
	- Utils are not tested at all (utils.py)
	- Serializers are not tested (serializers.py)
	- Sender.py is not tested. (sender.py)
	- Tasks are not tested. (tasks.py)
	- Filters not tested. (filters.py)

**PARTICIPANTS APP:**
	- Serializers are not tested (serializers.py)
	- Utils are not tested (utils.py)
	- Admin is not tested (admin.py)

**WEB APP:**
	- Serializers is not tested (serializers.py)
	- Admin not tested (admin.py)
	- URLs not tested (utils.py)


If the following test cases are written, the Code Coverage will be greater than 90% (>90%).
