import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { AuthComponent } from './auth.component';
import { HeaderStaticComponent } from '../partials/nav/header-static/header-static.component';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../global.service';
import { AuthService } from '../services/auth.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('AuthComponent', () => {
  let component: AuthComponent;
  let fixture: ComponentFixture<AuthComponent>;
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AuthComponent, HeaderStaticComponent ],
      providers: [
        GlobalService,
        AuthService
      ],
      imports: [ RouterTestingModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
