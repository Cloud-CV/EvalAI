import { Component, OnInit } from '@angular/core';
import { NGXLogger } from 'ngx-logger';

// import service
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { EndpointsService } from '../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-our-team',
  templateUrl: './our-team.component.html',
  styleUrls: ['./our-team.component.scss'],
})
export class OurTeamComponent implements OnInit {
  /**
   * Constructor.
   * @param apiService  ApiService Injection.
   * @param globalService  GlobalService Injection.
   * @param endpointsService  EndpointService Injection.
   */
  constructor(
    private apiService: ApiService,
    private globalService: GlobalService,
    private endpointsService: EndpointsService,
    private logger: NGXLogger
  ) {}

  /**
   * Core team type
   */
  coreTeamType: any = '';

  /**
   * Core team type
   */
  coreTeamList: any = [];

  /**
   * Contributing team type
   */
  contributingTeamType: any = '';

  /**
   * Contributing team type
   */
  contributingTeamList: any = [];

  /**
   * Core team details
   */
  coreTeamDetails: any = [];

  /**
   * Contributing team details
   */
  contributingTeamDetails: any = [];

  /**
   * No team found
   */
  noTeamDisplay: any = '';

  /**
   * Component on intialized.
   */
  ngOnInit() {
    this.fetchOurTeamMembers();
  }

  /**
   * Fetching team members
   */
  fetchOurTeamMembers() {
    const API_PATH = this.endpointsService.ourTeamURL();
    const SELF = this;
    SELF.apiService.getUrl(API_PATH).subscribe(
      (data) => {
        let results = data;
        if (results.length === 0) {
          // Hard coding our team members
          results = [
            {
              name: 'Rishabh Jain',
              description: 'Team Lead',
              email: 'rishabhjain@gatech.edu',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/IMG_6613.JPG',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/Rishabh_Jain.jpeg',
              github_url: 'https://github.com/RishabhJain2018',
              linkedin_url: 'https://www.linkedin.com/in/rishabhjain1795/',
              personal_website: 'https://rishabhjain2018.github.io/',
              team_type: 'Core Team',
            },
            {
              name: 'Deshraj Yadav',
              description: 'Team Lead',
              email: 'deshraj@vt.edu',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/bd8d1fe0-4e9a-40a0-9584-dd9fa7894a79.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/15775051_1334147123295477_4609249739680158814_o.jpg',
              github_url: 'http://github.com/deshraj',
              linkedin_url: 'https://www.linkedin.com/in/deshraj-yadav-34325975',
              personal_website: 'http://deshraj.github.io',
              team_type: 'Core Team',
            },
            {
              name: 'Harsh Agrawal',
              description: 'Project Manager',
              email: 'h.agrawal092@gmail.com',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/dp1.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/1965514_10152523766307739_2542282903877038889_o.jpg',
              github_url: 'https://github.com/dexter1691',
              linkedin_url: 'https://www.linkedin.com/in/harsh092/',
              personal_website: 'https://dexter1691.github.io/',
              team_type: 'Core Team',
            },
            {
              name: 'Devi Parikh',
              description: 'Advisor',
              email: 'parikh@gatech.edu',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/devi.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/15965604_10101311300574979_1155748140016787470_n.jpg',
              github_url: 'null',
              linkedin_url: 'https://www.linkedin.com/in/devi-parikh-71613a8/',
              personal_website: 'https://filebox.ece.vt.edu/~parikh/',
              team_type: 'Core Team',
            },
            {
              name: 'Dhruv Batra',
              description: 'Advisor',
              email: 'dbatra@gatech.edu',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/dhruv.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/12370908_10100934153600539_2116221676470914938_o.jpg',
              github_url: 'https://github.com/dhruvbatra',
              linkedin_url: 'null',
              personal_website: 'https://filebox.ece.vt.edu/~dbatra/',
              team_type: 'Core Team',
            },
            {
              name: 'Taranjeet',
              description: 'Lead Backend Developer',
              email: 'reachtotj@gmail.com',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/4302268.jpeg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/10178044_664063280345448_7169289118796237_n.jpg',
              github_url: 'http://github.com/trojan',
              linkedin_url: 'https://www.linkedin.com/in/taranjeet-singh-1577b858/',
              personal_website: 'http://trojan.github.io/',
              team_type: 'Contributors',
            },
            {
              name: 'Prithvijit Chattopadhyay',
              description: 'Backend Developer',
              email: 'prithvijitchattopadhyay@gmail.com',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/prithv1.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/18056475_1816935868332485_6070888708209307482_o.jpg',
              github_url: 'https://github.com/prithv1',
              linkedin_url: 'https://www.linkedin.com/in/prithvijit-chattopadhyay-260b2b54/',
              personal_website: 'https://prithv1.github.io/',
              team_type: 'Contributors',
            },
            {
              name: 'Akash Jain',
              description: 'Lead UI/UX',
              email: 'akajain993@gmail.com',
              headshot:
                'https://evalai.s3.amazonaws.com/media/headshots/' +
                'AAEAAQAAAAAAAAfFAAAAJDdjZTQ5MThmLTJlOTMtNGMxMS05NTFjLTI3NmZiMTA0ZDE3OQ.jpg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/13227264_948001968631519_3882689880500687242_o.jpg',
              github_url: 'https://github.com/aka-jain',
              linkedin_url: 'https://www.linkedin.com/in/jainakashin/',
              personal_website: 'http://www.jainakash.in/',
              team_type: 'Contributors',
            },
            {
              name: 'Shiv Baran',
              description: 'Lead Frontend',
              email: 'spyshiv@gmail.com',
              headshot: 'https://evalai.s3.amazonaws.com/media/headshots/7015220.jpeg',
              background_image:
                'https://evalai.s3.amazonaws.com/media/bg-images/12362825_836486476462466_3609928140833176026_o.jpg',
              github_url: 'https://github.com/spyshiv',
              linkedin_url: 'https://www.linkedin.com/in/shivbaran1/',
              personal_website: 'http://spyshiv.github.io/',
              team_type: 'Contributors',
            }
          ];
        }
        if (results.length !== 0) {
          const CORE_TEAM_LIST = [];
          const CONTRIBUTING_TEAM_LIST = [];
          for (let i = 0; i < results.length; i++) {
            if (results[i].team_type === 'Core Team') {
              SELF.coreTeamType = results[i].team_type;
              SELF.coreTeamList = CORE_TEAM_LIST.push(results[i]);
            } else if (results[i].team_type === 'Contributors') {
              SELF.contributingTeamType = results[i].team_type;
              SELF.contributingTeamList = CONTRIBUTING_TEAM_LIST.push(results[i]);
            }
            SELF.coreTeamDetails = CORE_TEAM_LIST;
            SELF.contributingTeamDetails = CONTRIBUTING_TEAM_LIST;
          }
        } else {
          SELF.noTeamDisplay = 'Team will be updated very soon !';
        }
      },
      (err) => {
        SELF.globalService.handleApiError(err);
      },
      () => this.logger.info('Ongoing challenges fetched!')
    );
  }
}
