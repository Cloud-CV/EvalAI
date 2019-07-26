import { Injectable, Output, EventEmitter } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable()
export class GlobalService {
  scrolledStateDefault = false;
  toastErrorCodes = [400, 500];
  authStorageKey = 'authtoken';
  redirectStorageKey = 'redirect';
  isLoading = false;
  private isLoadingSource = new BehaviorSubject(false);
  currentisLoading = this.isLoadingSource.asObservable();
  isConfirming = false;
  confirmDefault = {
    isConfirming: false,
    confirm: 'Yes',
    deny: 'Cancel',
    title: 'Are you sure?',
    confirmCallback: null,
    denyCallback: null
  };

  /**
   * Reusable modal default settings
   */
  isModalVisible = false;
  modalDefault = {
    isModalVisible: false,
    confirm: 'Confirm',
    deny: 'Cancel',
    title: 'Update Fields',
    confirmCallback: null,
    denyCallback: null,
    form: []
  };

  /**
   * Edit challenge phase modal default settings
   */
  isEditPhaseModalVisible = false;
  editPhaseModalDefault = {
    isEditPhaseModalVisible: false,
    confirm: 'Submit',
    deny: 'Cancel',
    title: 'Edit Challenge Phase Details',
    confirmCallback: null,
    denyCallback: null
  };

  /**
   * Title loader
   */
  loaderTitle = '';

  /**
   * Terms and conditions modal default settings
   */
  isTermsAndConditionsModalVisible = false;
  termsAndConditionsModalDefault = {
    isTermsAndConditionsModalVisible: false,
    confirm: 'Submit',
    deny: 'Cancel',
    title: 'Terms and Conditions',
    confirmCallback: null,
    denyCallback: null
  };

  private scrolledStateSource = new BehaviorSubject(this.scrolledStateDefault);
  currentScrolledState = this.scrolledStateSource.asObservable();
  private confirmSource = new BehaviorSubject(this.confirmDefault);
  currentConfirmParams = this.confirmSource.asObservable();
  private modalSource = new BehaviorSubject(this.modalDefault);
  currentModalParams = this.modalSource.asObservable();
  private editPhasemodalSource = new BehaviorSubject(this.editPhaseModalDefault);
  editPhaseModalParams = this.editPhasemodalSource.asObservable();
  private termsAndConditionsSource = new BehaviorSubject(this.termsAndConditionsModalDefault);
  termsAndConditionsModalParams = this.termsAndConditionsSource.asObservable();

  @Output() toast: EventEmitter<Object> = new EventEmitter();
  @Output() loading: EventEmitter<boolean> = new EventEmitter();
  @Output() logout: EventEmitter<boolean> = new EventEmitter();
  @Output() scrolltop: EventEmitter<Object> = new EventEmitter();

  /**
   * constructor
   */
  constructor() { }

  /**
   * Update Scrolled State.
   * @param s  New scrolled state.
   */
  scrolledStateChange(s) {
    this.scrolledStateSource.next(s);
  }

  /**
   * Store data in localStorage
   * @param key  Key for storing
   * @param value  Value for storing
   */
  storeData(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  /**
   * Get data from localStorage
   * @param key  fetch this key from storage.
   */
  getData(key) {
    if (localStorage.getItem(key) === null || localStorage.getItem(key) === 'undefined') {
      localStorage.removeItem(key);
      return false;
    } else {
      return JSON.parse(localStorage.getItem(key));
    }
  }

  /**
   * Delete key from localStorage
   * @param key  Delete this key from storage
   */
  deleteData(key) {
    localStorage.removeItem(key);
  }

  /**
   * Clear entire storage
   */
  resetStorage() {
    localStorage.clear();
  }

  /**
   * Fetch Auth Token
   */
  getAuthToken() {
    return this.getData(this.authStorageKey);
  }

  /**
   * Display Toast component
   * @param type  Type of toast- success/error/info
   * @param message  Message to be displayed
   * @param duration  Duration in seconds
   */
  showToast(type, message, duration = 5) {
    const TEMP = {
      type: type,
      message: message,
      duration: duration
    };
    this.toast.emit(TEMP);
  }

  /**
   * Toggle Loading component
   * @param loading  show or hide loading component
   */
  toggleLoading(loading) {
    if (loading !== this.isLoading) {
      this.isLoading = loading;
      this.isLoadingSource.next(loading);
    }
  }

  /**
   * Display confirm component
   * @param params  parameters for configuring confirm component (see markdown docs)
   */
  showConfirm(params) {
    if (!this.isConfirming) {
      this.isConfirming = true;
      const TEMP = { isConfirming: true};
      this.confirmSource.next(Object.assign({}, params, TEMP));
    }
  }

  /**
   * Hide confirm component
   */
  hideConfirm() {
    if (this.isConfirming) {
      this.isConfirming = false;
      const TEMP = { isConfirming: false};
      this.confirmSource.next(Object.assign({}, this.modalDefault, TEMP));
    }
  }

  /**
   * Display Reusable Modal Component
   * @param params  parameters for configuring reusable modal component (see markdown docs)
   */
  showModal(params) {
    if (!this.isModalVisible) {
      this.isModalVisible = true;
      const TEMP = { isModalVisible: true};
      this.modalSource.next(Object.assign({}, params, TEMP));
    }
  }

  /**
   * Display Edit Challenge Phase Modal Component
   * @param params  parameters for configuring edit challenge phase component (see markdown docs)
   */
  showEditPhaseModal(params) {
    if (!this.isEditPhaseModalVisible) {
      this.isEditPhaseModalVisible = true;
      const TEMP = { isEditPhaseModalVisible: true};
      this.editPhasemodalSource.next(Object.assign({}, params, TEMP));
    }
  }

  /**
   * Display terms and conditions Modal Component
   * @param params  parameters for configuring terms and conditions component (see markdown docs)
   */
  showTermsAndConditionsModal(params) {
    if (!this.isTermsAndConditionsModalVisible) {
      this.isTermsAndConditionsModalVisible = true;
      const TEMP = { isTermsAndConditionsModalVisible: true};
      this.termsAndConditionsSource.next(Object.assign({}, params, TEMP));
    }
  }

  /**
   * Hide Reusable Modal Component
   */
  hideModal() {
    if (this.isModalVisible) {
      this.isModalVisible = false;
      const TEMP = { isModalVisible: false};
      this.modalSource.next(Object.assign({}, this.modalDefault, TEMP));
    }
  }

  /**
   * Hide Edit Challenge Phase Modal Component
   */
  hideEditPhaseModal() {
    if (this.isEditPhaseModalVisible) {
      this.isEditPhaseModalVisible = false;
      const TEMP = { isEditPhaseModalVisible: false};
      this.editPhasemodalSource.next(Object.assign({}, this.editPhaseModalDefault, TEMP));
    }
  }

  /**
   * Hide terms and conditions Modal Component
   */
  hideTermsAndConditionsModal() {
    if (this.isTermsAndConditionsModalVisible) {
      this.isTermsAndConditionsModalVisible = false;
      const TEMP = { isTermsAndConditionsModalVisible: false};
      this.termsAndConditionsSource.next(Object.assign({}, this.termsAndConditionsModalDefault, TEMP));
    }
  }

  /**
   * This triggers the logout function in auth service (to avoid a cyclic dependency).
   */
  triggerLogout() {
    this.logout.emit();
  }

  /**
   * Scroll to top of the page
   */
  scrollToTop() {
    this.scrolltop.emit();
  }

  /**
   * Form Validation before submitting.
   * @param components  Expects a QueryList of form components.
   * @param callback  Form submission callback if fields pass validation.
   */
  formValidate(components, callback, self) {
    let requiredFieldMissing = false;
    components.map((item) => {
      if (item.isRequired && !item.isDirty) {
        item.isDirty = true;
      }
      if (item.isRequired && !item.isValid) {
        requiredFieldMissing = true;
      }
    });
    if (!requiredFieldMissing) {
       callback(self);
    }
  }

  /**
   * Get Form field values in the form of JSON
   * @param components  form components
   * @returns JSON of form item values
   */
  formFields(components) {
    const TEMP = {};
    components.map((item) => {
      if (item.type === 'file' && item.fileSelected != null) {
        TEMP[item.label] = item.fileSelected;
      }
      if (item.type !== 'file') {
        if (item.type === 'datetime') {
          const date = new Date(item.value);
          TEMP[item.label.toLowerCase()] = date.toISOString();
        } else {
          TEMP[item.label.toLowerCase()] = item.value;
        }
      }
    });
    return TEMP;
  }

  /**
   * Get Form field value for a label
   * @param components  form components
   * @param label  label to fetch
   * @returns value of form item
   */
  formValueForLabel(components, label) {
    let value = '';
    let valueFound = false;
    components.map((item) => {
      if (item.label.toLowerCase() === label.toLowerCase()) {
        value = item.value;
        valueFound = true;
      }
    });
    if (!valueFound) {
      console.error('Form value not found for ' + label);
      return null;
    } else {
      return value;
    }
  }

  /**
   * Set Form field value for a label
   * @param components  form components
   * @param label  label to fetch
   * @param value new value to be set
   * @returns value of form item
   */
  setFormValueForLabel(components, label, value) {
    let valueFound = false;
    components.map((item) => {
      if (item.label.toLowerCase() === label.toLowerCase()) {
        if (item.type === 'file') {
          item.fileValue = value;
          item.placeholder = '';
        } else {
          item.value = value;
        }
        valueFound = true;
      }
    });
    if (!valueFound) {
      console.error('Form value not found for ' + label);
    }
  }

  /**
   * Set Form item for a label
   * @param components  form components
   * @param label  label to fetch
   * @returns form item
   */
  formItemForLabel(components, label) {
    let value: any;
    let valueFound = false;
    components.map((item) => {
      if (item.label.toLowerCase() === label.toLowerCase()) {
        value = item;
        valueFound = true;
      }
    });
    if (!valueFound) {
      console.error('Form value not found for ' + label);
      return null;
    } else {
      return value;
    }
  }

  /**
   * Check if token is still valid
   * @param err  error object
   * @param toast  show/hide toast flag
   */
  checkTokenValidity(err, toast = true) {
    if (err.error !== null && typeof err.error === 'object' && err.error['detail']) {
      if (err.error['detail'].indexOf('Invalid token') !== -1 ||
          err.error['detail'].indexOf('Token has expired') !== -1) {
        this.triggerLogout();
        this.showToast('error', 'Token Invalid! Please Login again.', 5);
      }
    } else if (toast) {
      this.showToast('error', 'Something went wrong <' + err.status + '> ', 5);
    }
  }

  /**
   * Get Form field value for a label
   * @param components  form components
   * @param label  label to fetch
   * @returns value of form item
   */
  handleFormError(form, err, toast = true) {
    const ERR = err.error;
    if (this.toastErrorCodes.indexOf(err.status) > -1 && ERR !== null && typeof ERR === 'object') {
      console.error(err);
      for (const KEY in ERR) {
        if (KEY === 'non_field_errors') {
          this.showToast('error', ERR[KEY][0], 5);
        } else {
          const FORM_ITEM = this.formItemForLabel(form, KEY);
          if (FORM_ITEM) {
            FORM_ITEM.isValid = false;
            FORM_ITEM.message = ERR[KEY][0];
          }
        }
      }
    } else {
      this.handleApiError(err, toast);
    }
  }

  /**
   * Handle error from an API response
   * @param err  error object
   * @param toast  toast show flag
   */
  handleApiError(err, toast = true) {
    console.error(err);
    if (err.status === 401) {
      this.checkTokenValidity(err, toast);
    } else if (err.status === 403 && toast) {
      this.showToast('error', err.error['error'], 5);
    } else if (err.status === 404 && toast) {
      this.showToast('error', err.error['detail'], 5);
    } else if (err.status === 406 && toast) {
      this.showToast('error', err.error['error'], 5);
    } else if (toast) {
      this.showToast('error', 'Something went wrong <' + err.status + '> ', 5);
    }
  }

  /**
   * Get date string in 12 hour format from date object
   * @param date  date object
   * @returns 12 hour date string
   */
  formatDate12Hour(date) {
    let hours = date.getHours();
    let minutes = date.getMinutes();
    const AM_PM = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // the hour '0' should be '12'
    minutes = minutes < 10 ? '0' + minutes : minutes;
    const STR_TIME = date.toDateString() + ' ' + hours + ':' + minutes + ' ' + AM_PM;
    return STR_TIME;
  }

  /**
   * Get difference between two date objects
   * @param d1  date object
   * @param d2  date object
   * @returns difference in days
   */
  getDateDifference(d1, d2) {
    const T2 = d2.getTime();
    const T1 = d1.getTime();
    if (T2 >= T1) {
      return (T2 - T1) / (24 * 3600 * 1000);
    } else {
      return (T1 - T2) / (24 * 3600 * 1000);
    }
  }

  /**
   * Get Date difference string in seconds/minutes/hours/days/weeks/years
   * @param d1  date object
   * @param d2  date object
   * @returns date difference string
   */
  getDateDifferenceString(d1, d2) {
    const DIFF_DAYS = this.getDateDifference(d1, d2);
    if (DIFF_DAYS < 1) {
      const DIFF_HOURS = DIFF_DAYS * 24;
      if (DIFF_HOURS < 1) {
        const DIFF_MINUTES = DIFF_HOURS * 60;
        if (DIFF_MINUTES < 1) {
          const DIFF_SECONDS = DIFF_MINUTES * 60;
          return Math.floor(DIFF_SECONDS) + ' seconds';
        } else {
          return Math.floor(DIFF_MINUTES) + ' minute(s)';
        }
      } else {
        return Math.floor(DIFF_HOURS) + ' hour(s)';
      }
    } else {
      if (DIFF_DAYS > 100) {
        const DIFF_WEEKS = DIFF_DAYS / 7;
        if (DIFF_WEEKS > 104) {
          const DIFF_YEARS = DIFF_WEEKS / 52;
          return Math.floor(DIFF_YEARS) + ' year(s)';
        } else {
          return Math.floor(DIFF_WEEKS) + ' week(s)';
        }
      } else {
        return Math.floor(DIFF_DAYS) + ' day(s)';
      }
    }
  }

  /**
   * Form input email validator
   * @param email  email string
   * @returns boolean indicating valid/invalid email
   */
  validateEmail(email) {
    const RE = new RegExp (['^(([^<>()[\\]\\\.,;:\\s@\"]+(\\.[^<>()\\[\\]\\\.,;:\\s@\"]+)*)',
                        '|(".+"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.',
                        '[0-9]{1,3}\])|(([a-zA-Z\\-0-9]+\\.)+',
                        '[a-zA-Z]{2,}))$'].join(''));
    return RE.test(email);
  }

  /**
   * Form input text validator
   * @param text  text string
   * @returns boolean indicating valid/invalid text
   */
  validateText(text) {
    if (text.length >= 2) {
      return true;
    }
    return false;
  }

  /**
   * Form input number validator
   * @param integer  number integer
   * @returns boolean indicating valid/invalid text
   */
  validateInteger(integer) {
    return integer > 0;
  }

  /**
   * Form input password validator
   * @param password  password string
   * @returns boolean indicating valid/invalid password
   */
  validatePassword(password) {
    if (password.length >= 8) {
      return true;
    }
    return false;
  }

  /**
   * Start loader message
   * @param msg  string
   */
  startLoader(msg) {
    this.loaderTitle = msg;
  }

  /**
   * Stop loader msg
   */
  stopLoader() {
    this.loaderTitle = '';
  }
}
