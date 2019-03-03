import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ProfileComponent } from './profile.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { WindowService } from '../../services/window.service';
import { HttpClientModule } from '@angular/common/http';


describe('ProfileComponent', () => {
  let component: ProfileComponent;
  let fixture: ComponentFixture<ProfileComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ProfileComponent, HeaderStaticComponent, FooterComponent ],
      providers: [ GlobalService, AuthService, WindowService, ApiService, EndpointsService],
      imports: [ HttpClientModule, RouterTestingModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
