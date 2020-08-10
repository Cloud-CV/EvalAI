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
import { Router, Routes } from '@angular/router';
import { NotFoundComponent } from '../not-found/not-found.component';
import { LoginComponent } from '../auth/login/login.component';
import { FormsModule } from '@angular/forms';

const routes: Routes = [
  {
    path: '',
    component: ProfileComponent,
  },
  {
    path: 'auth/login',
    component: LoginComponent,
  },
  {
    path: '404',
    component: NotFoundComponent,
  },
  {
    path: '**',
    redirectTo: '/404',
    pathMatch: 'full',
  },
];

describe('ProfileComponent', () => {
  let component: ProfileComponent;
  let fixture: ComponentFixture<ProfileComponent>;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ProfileComponent, HeaderStaticComponent, FooterComponent, NotFoundComponent, LoginComponent],
      providers: [GlobalService, AuthService, WindowService, ApiService, EndpointsService],
      imports: [HttpClientModule, RouterTestingModule.withRoutes(routes), FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });
});
