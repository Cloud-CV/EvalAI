import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ContactComponent } from './contact.component';
import { HeaderStaticComponent } from '../../components/nav/header-static/header-static.component';
import { ToastComponent } from '../../components/utility/toast/toast.component';
import { InputComponent } from '../../components/utility/input/input.component';
import { MockWindowService } from '../../services/mock.window.service';
import { WindowService } from '../../services/window.service';
import { GlobalService } from '../../services/global.service';
import { AuthService } from '../../services/auth.service';
import { EndpointsService } from '../../services/endpoints.service';
import { ApiService } from '../../services/api.service';
import {ActivatedRoute, Router, Routes} from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { FooterComponent } from '../../components/nav/footer/footer.component';
import { RouterTestingModule } from '@angular/router/testing';
import Global = NodeJS.Global;

const routes: Routes = [
  {
    path: 'contact',
    component: ContactComponent
  }
];


describe('ContactComponent', () => {
  let router: Router;
  let component: ContactComponent;
  let fixture: ComponentFixture<ContactComponent>;
  const fakeActivatedRoute = {
    snapshot: { data: { } }
  } as ActivatedRoute;

  let authService: AuthService;
  let apiService: ApiService;
  let globalService: GlobalService;

  beforeEach(async(() => {
    // Google Maps API errors out when Karma tries to load it.
    // As a result Components are not created and the tests fail.
    // Mocking the loadJS function in window service to prevent that.
    const MOCK_SERVICE = new MockWindowService(null);
    TestBed.configureTestingModule({
      imports: [ HttpClientModule, RouterTestingModule.withRoutes(routes) ],
      declarations: [ ContactComponent, HeaderStaticComponent, InputComponent, ToastComponent, FooterComponent ],
      providers: [
        GlobalService,
        AuthService,
        ApiService,
        {provide: WindowService, useValue: MOCK_SERVICE },
        EndpointsService
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    authService = TestBed.get(AuthService);
    apiService = TestBed.get(ApiService);
    globalService = TestBed.get(GlobalService);
    fixture = TestBed.createComponent(ContactComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.ngZone.run(() => {
      router.navigate(['/contact']).then(() => {
        fixture.detectChanges();
        expect(component).toBeTruthy();
      });
    });
  });
});
