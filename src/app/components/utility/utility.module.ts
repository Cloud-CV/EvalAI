import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OwlDateTimeModule, OwlNativeDateTimeModule } from 'ng-pick-datetime';
import { FroalaEditorModule, FroalaViewModule } from 'angular-froala-wysiwyg';
import { RouterModule } from '@angular/router';
import { MatChipsModule, MatTableModule, MatMenuModule, MatSelectModule, MatIconModule, MatDividerModule, MatCheckboxModule } from '@angular/material';
import { FormsModule } from '@angular/forms';

// import components
import { CardlistComponent } from './cardlist/cardlist.component';
import { ConfirmComponent } from './confirm/confirm.component';
import { ForceloginComponent } from './forcelogin/forcelogin.component';
import { InputComponent } from './input/input.component';
import { LoadingComponent } from './loading/loading.component';
import { ModalComponent } from './modal/modal.component';
import { SelectphaseComponent } from './selectphase/selectphase.component';
import { SideBarComponent } from './side-bar/side-bar.component';
import { ToastComponent } from './toast/toast.component';

// import Directives
import { EmailValidatorDirective } from '../../Directives/email.validator';
import { PasswordMismatchValidatorDirective } from '../../Directives/password.validator';

@NgModule({
declarations: [
  CardlistComponent,
  ConfirmComponent,
  ForceloginComponent,
  InputComponent,
  LoadingComponent,
  ModalComponent,
  SelectphaseComponent,
  SideBarComponent,
  ToastComponent,
  EmailValidatorDirective,
  PasswordMismatchValidatorDirective
],
imports: [
  CommonModule,
  FormsModule,
  MatChipsModule,
  MatTableModule,
  MatMenuModule,
  MatSelectModule,
  MatIconModule,
  MatDividerModule,
  MatCheckboxModule,
  RouterModule,
  OwlDateTimeModule,
  OwlNativeDateTimeModule,
  FroalaEditorModule.forRoot(),
  FroalaViewModule.forRoot(),
],
exports: [

  CardlistComponent,
  ConfirmComponent,
  ForceloginComponent,
  InputComponent,
  LoadingComponent,
  ModalComponent,
  SelectphaseComponent,
  SideBarComponent,
  ToastComponent,
  EmailValidatorDirective,
  PasswordMismatchValidatorDirective
],
schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})
export class UtilityModule {}
