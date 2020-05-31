import {Directive} from '@angular/core';
import {AbstractControl, NG_VALIDATORS, ValidationErrors, Validator} from '@angular/forms';

@Directive({
  selector: '[appComparePassword]',
  providers: [{ provide: NG_VALIDATORS, useExisting: PasswordMismatchValidatorDirective, multi: true }]
})
export class PasswordMismatchValidatorDirective implements Validator {
  validate(control: AbstractControl): ValidationErrors {
    const pswrd = control.get('password');
    const confirmpswrd = control.get('confirm_password');
    return pswrd && confirmpswrd && pswrd.value !== confirmpswrd.value ? { 'passwordMismatch': true } : null;
  }
}
