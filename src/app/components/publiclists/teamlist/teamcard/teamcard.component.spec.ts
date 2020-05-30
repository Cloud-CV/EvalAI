import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { EventEmitter } from '@angular/core';

import { TeamcardComponent } from './teamcard.component';
import { GlobalService } from '../../../../services/global.service';
import { ApiService } from '../../../../services/api.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientModule } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { AuthService } from '../../../../services/auth.service';
import { EndpointsService } from '../../../../services/endpoints.service';

describe('TeamcardComponent', () => {
  let component: TeamcardComponent;
  let fixture: ComponentFixture<TeamcardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TeamcardComponent ],
      providers: [ GlobalService, ApiService, AuthService, EndpointsService ],
      imports: [ RouterTestingModule, HttpClientModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TeamcardComponent);
    component = fixture.componentInstance;
    component.team = {members: []};
    component.selected = false;
    component.isOnChallengePage = false;
    component.deleteTeamCard = new EventEmitter<any>();
    component.deleteMemberCard = new EventEmitter<any>();
    component.selectTeamCard = new EventEmitter<any>();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
