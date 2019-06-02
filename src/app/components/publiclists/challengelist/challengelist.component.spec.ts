import {async, ComponentFixture, fakeAsync, TestBed, tick} from '@angular/core/testing';
import { ChallengelistComponent } from './challengelist.component';
import { CardlistComponent } from '../../utility/cardlist/cardlist.component';
import { ChallengecardComponent } from './challengecard/challengecard.component';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { ChallengeService } from '../../../services/challenge.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';
import { ForceloginComponent } from '../../utility/forcelogin/forcelogin.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import {Router, Routes} from '@angular/router';

import {PubliclistsComponent} from '../publiclists.component';

import {By} from '@angular/platform-browser';

const routes: Routes = [
  {
    path: 'challenge',
    redirectTo: 'challenges/all'
  },
  {path: 'challenges/all', component: ChallengelistComponent},
  {path: 'challenges/me', component: ChallengelistComponent},
  {
    path: '**',
    redirectTo: '/challenges/all',
    pathMatch: 'full'
  }
];


describe('ChallengelistComponent', () => {
  let component: ChallengelistComponent;
  let fixture: ComponentFixture<ChallengelistComponent>;
  let authService: AuthService;
  let globalService: GlobalService;
  let challengeService: ChallengeService;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ HttpClientModule, RouterTestingModule.withRoutes(routes) ],
      declarations: [ ChallengelistComponent,
        CardlistComponent,
        ChallengecardComponent,
        ForceloginComponent,
        PubliclistsComponent],
      providers: [ GlobalService,
        ApiService,
        AuthService,
        ChallengeService,
        EndpointsService ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(ChallengelistComponent);
    authService = TestBed.get(AuthService);
    globalService = TestBed.get(GlobalService);
    challengeService = TestBed.get(ChallengeService);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    spyOn(authService, 'isLoggedIn').and.returnValue(true);
    fixture.detectChanges();

    expect(component).toBeTruthy();
  });

});
