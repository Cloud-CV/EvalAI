import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { OurTeamComponent } from './our-team.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { FooterComponent } from '../nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { HttpClientModule } from '@angular/common/http';

describe('OurTeamComponent', () => {
  let component: OurTeamComponent;
  let fixture: ComponentFixture<OurTeamComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ OurTeamComponent, FooterComponent, HeaderStaticComponent ],
      imports: [ HttpClientModule, RouterTestingModule ],
      providers: [ GlobalService, AuthService, EndpointsService, ApiService],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(OurTeamComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
