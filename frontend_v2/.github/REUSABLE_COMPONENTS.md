# Reusable Components

Please see [Code Structure Guide](https://github.com/Cloud-CV/EvalAI-ngx/blob/master/.github/CODE_STRUCTURE.md) before this to have an overview about the project.


All of the following components are inside `src/app/components`.

---

### TOAST
> PATH: `utility/toast`

A custom notification component which displays success, error and info messages from the platform to the user.

Usage:
- Inject **GlobalService** in your component or service **.ts** file like:
```
constructor(private globalService: GlobalService) {
...
```
- Call the _showToast_ function like:
```
this.globalService.showToast(type, message, duration);
```
	- type: (Type of toast- 'success'/'error'/'info')
	- message: 'Message' to be displayed
	- duration: duration in seconds

---

### HEADER
> PATH: `nav/header-static`

Responsive Navigation Header with jump links.

Usage:
- Add the following in your component **.html** file:
```
<app-header-static></app-header-static>
```

---

### FOOTER
> PATH: `nav/footer`

Responsive Navigation Footer with jump links.

Usage:
- Add the following in your component **.html** file:
```
<app-footer></app-footer>
```

---

### LOADING
> PATH: `utility/loading`

Loading gif overlay component (used in API calls wrapper right now)

Usage:
- Inject **GlobalService** in your component or service **.ts** file like:
```
constructor(private globalService: GlobalService) {
...
```
- Call this function to show loading
```
this.globalService.toggleLoading(true)
```
- Call this function to hide loading
```
this.globalService.toggleLoading(false)
```

---

### Forcelogin
> PATH: `utility/forcelogin`

Used on pages with sections which should only be accessible to logged-in users. Users are redirected to the correct page when they log in.

Usage:
- Add the following to your component **.html** file:
```
<app-forcelogin *ngIf="!isLoggedIn" [path]="routerPublic.url">
```
	- isLoggedIn is a boolean inside the component which is set if the user is logged in like:
	```
	ngOnInit() {
    if (this.authService.isLoggedIn()) {
      this.isLoggedIn = true;
    }
    ...
	```
	- _path_ - This is the path where the user should be redirected to after logging in.

---

### Input
> PATH: `utility/input`

Form item component for making it easy to build forms and validations with support for input types: text, password, email and file.

Usage:
- Add the following to your component **.html** file:
```
<app-input [isRequired]="true" [label]="'Username'" [type]="'text'" [theme]="'dark'" [icon]="'assets/images/username_dark.png'"  #formlogin></app-input>
```
	- _#formlogin_ - Is used for grouping items into a single form. This can be used for making use of predefined validation functions like: 
	```
	@ViewChildren('formlogin')
  	components: QueryList<InputComponent>;

  	this.globalService.formValidate(components, this.functionAfterValidation, this);

  	functionAfterValidation (self) {
  	// AJAX call to backend
  	...
	```
	See `login.component.ts` or `contact.component.ts` for example usages.

	- Default validation functions are used for all input types. Make use of the input parameter `[validate]="yourFunctionThatReturnsBoolean"`

---

### CONFIRM
> PATH: `utility/confirm`

Typescript callable Confirm modal for confirming from the user before making the operation (like delete/logout operations).

Usage:
- Inject **GlobalService** in your component or service **.ts** file like:
```
constructor(private globalService: GlobalService) {
...
```

- Add the following to your component or service **.ts** file:
```
apiCall = () => {
	// Confirmed callback
};
const PARAMS = {
  title: 'Would you like to remove yourself ?',
  content: 'Note: This action will remove you from the team.',
  confirm: 'Yes',
  deny: 'Cancel',
  confirmCallback: apiCall
};
SELF.globalService.showConfirm(PARAMS);
```

---

### MODAL
> PATH: `utility/modal`

Typescript callable custom Modal with form items to be submitted (like update operations)

Usage:
- Inject **GlobalService** in your component or service **.ts** file like:
```
constructor(private globalService: GlobalService) {
...
```
- Add the following to your component or service **.ts** file:
```
apiCall = (params) => {
	// params contains values from the validated form like:
	// { first_name: value, last_name: value ... }
	// Confirmed callback
};
const PARAMS = {
  title: 'Update Profile',
  content: '',
  confirm: 'Submit',
  deny: 'Cancel',
  form: [
    {
      isRequired: true,
      label: 'first_name',
      placeholder: 'First Name',
      type: 'text',
      value: this.user['first_name']
    },
    {
      isRequired: true,
      label: 'last_name',
      placeholder: 'Last Name',
      type: 'text',
      value: this.user['last_name']
    },
    {
      isRequired: true,
      label: 'affiliation',
      placeholder: 'Affiliated To',
      type: 'text',
      value: this.user['affiliation']
    }
  ],
  confirmCallback: apiCall
};
SELF.globalService.showModal(PARAMS);
```
This makes use of the [input](#input) component discussed above. It performs validations on the form elements before returning the values to the _confirmCallback_ function.

---