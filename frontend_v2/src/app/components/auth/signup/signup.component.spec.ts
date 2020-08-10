import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { SignupComponent } from './signup.component';
import { InputComponent } from '../../../components/utility/input/input.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { WindowService } from '../../../services/window.service';
import { ApiService } from '../../../services/api.service';
import { HttpClientModule } from '@angular/common/http';
import { EndpointsService } from '../../../services/endpoints.service';
import { FormsModule } from '@angular/forms';

describe('SignupComponent', () => {
  let component: SignupComponent;
  let fixture: ComponentFixture<SignupComponent>;
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [SignupComponent, InputComponent],
      providers: [GlobalService, AuthService, WindowService, ApiService, EndpointsService],
      imports: [RouterTestingModule, HttpClientModule, FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SignupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
