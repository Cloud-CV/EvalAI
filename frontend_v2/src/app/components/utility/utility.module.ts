import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OwlDateTimeModule, OwlNativeDateTimeModule } from 'ng-pick-datetime';
import { RouterModule } from '@angular/router';
import { MatChipsModule, MatTableModule, MatMenuModule, MatSelectModule, MatIconModule, MatDividerModule, MatCheckboxModule } from '@angular/material';
import { FormsModule } from '@angular/forms';

// import components
import { ConfirmComponent } from './confirm/confirm.component';
import { ForceloginComponent } from './forcelogin/forcelogin.component';
import { InputComponent } from './input/input.component';
import { LoadingComponent } from './loading/loading.component';
import { SelectphaseComponent } from './selectphase/selectphase.component';
import { SideBarComponent } from './side-bar/side-bar.component';


@NgModule({
  declarations: [
    ForceloginComponent,
    InputComponent,
    SideBarComponent,
    ConfirmComponent,
    LoadingComponent,
    SelectphaseComponent,

  ],
  imports: [
    CommonModule,
    OwlDateTimeModule,
    OwlNativeDateTimeModule,
    FormsModule,
    RouterModule,
    MatSelectModule,
    MatChipsModule,
    MatTableModule,
    MatDividerModule,
    MatMenuModule,
    MatIconModule,
    MatCheckboxModule
  ],

  exports: [
    ForceloginComponent,
    InputComponent,
    OwlDateTimeModule,
    OwlNativeDateTimeModule,
    SideBarComponent,
    ConfirmComponent,
    LoadingComponent,
    SelectphaseComponent,
  ]
})
export class UtilityModule { }
