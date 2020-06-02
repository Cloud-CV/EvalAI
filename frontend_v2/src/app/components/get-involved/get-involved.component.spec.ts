import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { GetInvolvedComponent } from './get-involved.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ActivatedRoute, Router } from '@angular/router';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';
import { ApiService } from '../../services/api.service';
import { HttpClientModule } from '@angular/common/http';

describe('GetInvolvedComponent', () => {
  let component: GetInvolvedComponent;
  let fixture: ComponentFixture<GetInvolvedComponent>;
  let globalService;
  let globalServiceSpy;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ GetInvolvedComponent, HeaderStaticComponent, FooterComponent ],
      providers: [
        GlobalService,
        AuthService,
        ApiService,
        EndpointsService
      ],
      imports: [ RouterTestingModule, HttpClientModule ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GetInvolvedComponent);
    globalService = TestBed.get(GlobalService);
    globalServiceSpy = spyOn(globalService, 'scrollToTop');
    component = fixture.componentInstance;

    expect(globalServiceSpy).not.toHaveBeenCalled();
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call scrollToTop method of global service', () => {
    expect(globalServiceSpy).toHaveBeenCalledTimes(1);
  });
});
