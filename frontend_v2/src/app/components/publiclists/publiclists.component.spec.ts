import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PubliclistsComponent } from './publiclists.component';
import { ActivatedRoute, Router, Routes } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../services/global.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { TeamlistComponent } from './teamlist/teamlist.component';
import { ChallengelistComponent } from './challengelist/challengelist.component';
import { EndpointsService } from '../../services/endpoints.service';
import { AuthService } from '../../services/auth.service';
import { NotFoundComponent } from '../not-found/not-found.component';
import { ApiService } from '../../services/api.service';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

const routes: Routes = [
  {
    path: 'teams',
    component: PubliclistsComponent,
    children: [
      { path: '', redirectTo: 'participants', pathMatch: 'full' },
      { path: 'participants', component: TeamlistComponent },
      { path: 'hosts', component: TeamlistComponent },
    ],
  },
  {
    path: 'challenges',
    component: PubliclistsComponent,
    children: [
      { path: '', redirectTo: 'all', pathMatch: 'full' },
      { path: 'all', component: ChallengelistComponent },
      { path: 'me', component: ChallengelistComponent },
    ],
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

describe('PubliclistsComponent', () => {
  let component: PubliclistsComponent;
  let fixture: ComponentFixture<PubliclistsComponent>;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule.withRoutes(routes), HttpClientModule, FormsModule],
      declarations: [PubliclistsComponent, ChallengelistComponent, TeamlistComponent, NotFoundComponent],
      providers: [GlobalService, EndpointsService, AuthService, ApiService],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(PubliclistsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
