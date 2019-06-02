import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PubliclistsComponent } from './publiclists.component';
import {ActivatedRoute, Router, Routes} from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../services/global.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import {TeamlistComponent} from './teamlist/teamlist.component';
import {ChallengelistComponent} from './challengelist/challengelist.component';

const routes: Routes = [

  {
    path: 'teams',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'participants', pathMatch: 'full'},
      {path: 'participants', component: TeamlistComponent},
      {path: 'hosts', component: TeamlistComponent}
    ]
  },
  {
    path: 'challenges',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'all', pathMatch: 'full'},
      {path: 'all', component: ChallengelistComponent},
      {path: 'me', component: ChallengelistComponent}
    ]
  },
];



describe('PubliclistsComponent', () => {
  let component: PubliclistsComponent;
  let fixture: ComponentFixture<PubliclistsComponent>;
  let router: Router;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ RouterTestingModule.withRoutes(routes) ],
      declarations: [ PubliclistsComponent, ChallengelistComponent, TeamlistComponent ],
      providers: [ GlobalService ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
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
