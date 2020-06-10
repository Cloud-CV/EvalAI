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
  let endpointsService;
  let apiService;
  let endpointsServiceSpy;
  let fetchOurTeamMembersSpy;
  let apiServiceSpy;

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
    endpointsService = TestBed.get(EndpointsService);
    apiService = TestBed.get(ApiService);
    component = fixture.componentInstance;
    fetchOurTeamMembersSpy = spyOn(component, 'fetchOurTeamMembers').and.callThrough();
    endpointsServiceSpy = spyOn(endpointsService, 'ourTeamURL').and.callThrough();
    apiServiceSpy = spyOn(apiService, 'getUrl').and.callThrough();

    expect(fetchOurTeamMembersSpy).not.toHaveBeenCalled();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call fetchOurTeamMembers method on init', () => {
    expect(fetchOurTeamMembersSpy).toHaveBeenCalledTimes(1);
    expect(endpointsServiceSpy).toHaveBeenCalled();
    const expectedTeamUrl = 'web/team/';
    expect(apiServiceSpy).toHaveBeenCalledWith(expectedTeamUrl);
  });

});
