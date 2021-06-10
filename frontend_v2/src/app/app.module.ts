import { BrowserModule, HAMMER_GESTURE_CONFIG } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { GestureConfig } from '@angular/material';
import { HttpClientModule } from '@angular/common/http';
import { QuillModule } from 'ngx-quill';
import { LoggerModule, NgxLoggerLevel } from 'ngx-logger';

// Import services
import { WindowService } from './services/window.service';
import { ApiService } from './services/api.service';
import { GlobalService } from './services/global.service';
import { ChallengeService } from './services/challenge.service';
import { EndpointsService } from './services/endpoints.service';

// Import Components
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { AuthService } from './services/auth.service';
import { ModalComponent } from './components/utility/modal/modal.component';
import { ToastComponent } from './components/utility/toast/toast.component';
import { EditphasemodalComponent } from './components/challenge/challengephases/editphasemodal/editphasemodal.component';
import { TermsAndConditionsModalComponent } from './components/challenge/challengeparticipate/terms-and-conditions-modal/terms-and-conditions-modal.component';

// import module
import { SharedModule } from './shared/shared.module';
import { environment } from '../environments/environment';

@NgModule({
  declarations: [
    AppComponent,
    ModalComponent,
    ToastComponent,
    EditphasemodalComponent,
    TermsAndConditionsModalComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    SharedModule,
    HttpClientModule,
    QuillModule.forRoot({
      modules: {
        toolbar: [
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ header: 1 }, { header: 2 }], // custom button values
          [{ list: 'ordered' }, { list: 'bullet' }], // superscript/subscript
          [{ indent: '-1' }, { indent: '+1' }], // outdent/indent
          [{ direction: 'rtl' }],
          [{ header: [1, 2, 3, 4, 5, 6, false] }],
          [{ align: [] }],
          ['link', 'image'],
        ],
      },
    }),
    LoggerModule.forRoot({
      level: !environment.production ? NgxLoggerLevel.TRACE : NgxLoggerLevel.OFF,
      serverLogLevel: NgxLoggerLevel.ERROR,
    }),
  ],
  providers: [
    WindowService,
    AuthService,
    ApiService,
    GlobalService,
    ChallengeService,
    EndpointsService,
    { provide: HAMMER_GESTURE_CONFIG, useClass: GestureConfig },
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  bootstrap: [AppComponent],
})
export class AppModule {}
