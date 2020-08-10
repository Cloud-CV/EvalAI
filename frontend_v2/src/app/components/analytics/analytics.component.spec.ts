import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalyticsComponent } from './analytics.component';
import { SideBarComponent } from '../utility/side-bar/side-bar.component';
import { FooterComponent } from '../nav/footer/footer.component';
import { AuthService } from '../../services/auth.service';
import { GlobalService } from '../../services/global.service';
import { EndpointsService } from '../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { Routes } from '@angular/router';
import { NotFoundComponent } from '../not-found/not-found.component';
import { ApiService } from '../../services/api.service';
import { HeaderStaticComponent } from '../nav/header-static/header-static.component';

const routes: Routes = [
  {
    path: '',
    component: AnalyticsComponent,
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

describe('AnalyticsComponent', () => {
  let component: AnalyticsComponent;
  let fixture: ComponentFixture<AnalyticsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [AnalyticsComponent, SideBarComponent, FooterComponent, HeaderStaticComponent, NotFoundComponent],
      providers: [AuthService, GlobalService, EndpointsService, ApiService],
      imports: [HttpClientModule, RouterTestingModule.withRoutes(routes)],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AnalyticsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
