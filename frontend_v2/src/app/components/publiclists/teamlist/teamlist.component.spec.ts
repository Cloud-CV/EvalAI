import { async, ComponentFixture, fakeAsync, getTestBed, TestBed, tick } from '@angular/core/testing';

import { TeamlistComponent } from './teamlist.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { Router, Routes } from '@angular/router';

import { PubliclistsComponent } from '../publiclists.component';
import { By } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { NotFoundComponent } from '../../not-found/not-found.component';

const routes: Routes = [
  { path: '/teams/participants', component: TeamlistComponent },
  { path: '/teams/hosts', component: TeamlistComponent },
  {
    path: 'challenge-create',
    redirectTo: '/teams/hosts',
    pathMatch: 'full',
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

describe('TeamlistComponent', () => {
  let component: TeamlistComponent;
  let fixture: ComponentFixture<TeamlistComponent>;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [TeamlistComponent, NotFoundComponent],
      providers: [GlobalService, ApiService, AuthService, ChallengeService, EndpointsService],
      imports: [RouterTestingModule.withRoutes(routes), HttpClientModule, FormsModule],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(TeamlistComponent);
    component = fixture.componentInstance;
  });

  it('should create', fakeAsync(() => {
    router.navigate(['/teams/hosts']);
    tick();

    fixture.detectChanges();

    expect(component).toBeTruthy();
  }));
});
