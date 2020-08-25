import { Directive } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, ValidationErrors, Validator } from '@angular/forms';
import { GlobalService } from '../services/global.service';

@Directive({
  selector: '[appValidateEmail]',
  providers: [{ provide: NG_VALIDATORS, useExisting: EmailValidatorDirective, multi: true }],
})
export class EmailValidatorDirective implements Validator {
  constructor(private globalService: GlobalService) {}

  validate(control: AbstractControl): ValidationErrors {
    const email = control.get('email');
    if (email) {
      return this.globalService.validateEmail(email.value) ? null : { InvalidEmail: true };
    }
    return null;
  }
}
