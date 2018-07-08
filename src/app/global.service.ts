import { Injectable, Output, EventEmitter } from '@angular/core';

@Injectable()
export class GlobalService {
  scrolledState = false;
  toastErrorCodes = [400, 500];
  @Output() change: EventEmitter<boolean> = new EventEmitter();
  @Output() toast: EventEmitter<Object> = new EventEmitter();
  @Output() scrolltop: EventEmitter<Object> = new EventEmitter();
  constructor() { }
  scrolledStateChange(s) {
    this.scrolledState = s;
    this.change.emit(this.scrolledState);
  }
  storeData(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }
  getData(key) {
    if (localStorage.getItem(key) === null) {
      return false;
    } else {
      return JSON.parse(localStorage.getItem(key));
    }
  }
  deleteData(key) {
    localStorage.removeItem(key);
  }

  resetStorage() {
    localStorage.clear();
  }

  getAuthToken() {
    return this.getData('authtoken');
  }

  showToast(type, message, duration = 5) {
    const TEMP = {
      type: type,
      message: message,
      duration: duration
    };
    this.toast.emit(TEMP);
  }

  scrollToTop() {
    this.scrolltop.emit();
  }

  /**
   * Form Validation before submitting.
   * @param {components} Expects a QueryList of form components.
   * @param {callback} Form submission callback if fields pass validation.
   */
  formValidate(components, callback, self) {
    let requiredFieldMissing = false;
    components.map((item) => {
      if (item.isRequired && !item.isDirty) {
        item.isDirty = true;
      }
      if (!item.isValid) {
        requiredFieldMissing = true;
      }
    });
    if (!requiredFieldMissing) {
       callback(self);
    }
  }


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

  handleFormError(form, err) {
    console.error(err);
    const ERR = err.error;
    if (this.toastErrorCodes.indexOf(err.status) > -1 && ERR !== null && typeof ERR === 'object') {
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
      this.showToast('error', 'Something went wrong <' + err.status + '> ', 5);
    }
  }

  validateEmail(email) {
    const RE = new RegExp (['^(([^<>()[\\]\\\.,;:\\s@\"]+(\\.[^<>()\\[\\]\\\.,;:\\s@\"]+)*)',
                        '|(".+"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.',
                        '[0-9]{1,3}\])|(([a-zA-Z\\-0-9]+\\.)+',
                        '[a-zA-Z]{2,}))$'].join(''));
    return RE.test(email);
  }
  validateText(text) {
    if (text.length >= 2) {
      return true;
    }
    return false;
  }
  validatePassword(password) {
    if (password.length >= 8) {
      return true;
    }
    return false;
  }
}
